"""
Tests for /studies endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import copy
import datetime
import json
import logging
import random
import threading
from string import ascii_lowercase
from typing import Any, Sequence
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.models.study_selections.study import (
    RegistryIdentifiersJsonModel,
    Study,
    StudyCreateInput,
    StudyIdentificationMetadataJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
)
from clinical_mdr_api.models.study_selections.study_selection import EndpointUnitsInput
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
    input_metadata_in_study,
)
from clinical_mdr_api.tests.integration.utils.utils import (
    CT_CODELIST_UIDS,
    PROJECT_NUMBER,
    TestUtils,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_USERNAME
from clinical_mdr_api.tests.utils.checks import (
    assert_response_status_code,
    parse_json_response,
)
from common.config import settings

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study

day_unit_definition: UnitDefinitionModel
days_unit_definition: UnitDefinitionModel
week_unit_definition: UnitDefinitionModel
ct_term_study_standard_test: ct_term.CTTerm
study_with_subparts: Study
subpart_studies: Sequence[Study]
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studies.api"
    inject_and_clear_db(db_name)
    global test_data_dict
    _, test_data_dict = inject_base_data()
    global day_unit_definition
    day_unit_definition = TestUtils.get_unit_by_uid(
        unit_uid=TestUtils.get_unit_uid_by_name(unit_name="day")
    )
    global days_unit_definition
    days_unit_definition = TestUtils.get_unit_by_uid(
        unit_uid=TestUtils.get_unit_uid_by_name(unit_name="days")
    )
    global week_unit_definition
    week_unit_definition = TestUtils.get_unit_by_uid(
        unit_uid=TestUtils.get_unit_uid_by_name(unit_name="week")
    )

    global study
    study = TestUtils.create_study()

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    # Create a study selection

    # NUll flavor codelist
    ct_term_codelist = create_codelist(
        name="Null Flavor",
        uid="CTCodelist",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="NULLFLVR",
    )

    global ct_term_study_standard_test
    na_name = "Not Applicable"
    na_submvalue = "NA"
    ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        submission_value=na_submvalue,
        sponsor_preferred_name=na_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime.datetime(2020, 3, 25, tzinfo=datetime.timezone.utc),
        approve=True,
    )

    # yes no response codelist
    yesno_codelist = create_codelist(
        name="YesNo",
        uid="C66742",
        catalogue=catalogue_name,
        library=library_name,
    )
    TestUtils.create_ct_term(
        codelist_uid=yesno_codelist.codelist_uid,
        submission_value="Y",
        sponsor_preferred_name="Yes",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime.datetime(2020, 3, 25, tzinfo=datetime.timezone.utc),
        approve=True,
        term_uid="C49488",
    )
    TestUtils.create_ct_term(
        codelist_uid=yesno_codelist.codelist_uid,
        submission_value="N",
        sponsor_preferred_name="No",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime.datetime(2020, 3, 25, tzinfo=datetime.timezone.utc),
        approve=True,
        term_uid="C49487",
    )

    cdisc_package_name = "SDTM CT 2020-03-27"

    TestUtils.create_ct_package(
        catalogue=catalogue_name,
        name=cdisc_package_name,
        approve_elements=False,
        effective_date=datetime.datetime(2020, 3, 27, tzinfo=datetime.timezone.utc),
    )

    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uid": ct_term_study_standard_test.term_uid,
        "date": datetime.datetime(2020, 3, 26, tzinfo=datetime.timezone.utc),
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


def test_get_study_by_uid(api_client):
    response = api_client.get(
        f"/studies/{study.uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == study.uid
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"] is not None
    assert res["current_metadata"]["version_metadata"] is not None
    assert res["current_metadata"].get("high_level_study_design") is None
    assert res["current_metadata"].get("study_population") is None
    assert res["current_metadata"].get("study_intervention") is None
    assert res["current_metadata"].get("study_description") is not None

    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["high_level_study_design", "study_intervention"],
            "exclude_sections": ["identification_metadata"],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == study.uid
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"].get("identification_metadata") is None
    assert res["current_metadata"]["version_metadata"] is not None
    assert res["current_metadata"].get("high_level_study_design") is not None
    assert res["current_metadata"].get("study_population") is None
    assert res["current_metadata"].get("study_intervention") is not None
    assert res["current_metadata"].get("study_description") is not None

    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["non-existent section"],
            "exclude_sections": ["non-existent section"],
        },
    )
    assert_response_status_code(response, 400)


def test_get_study_fields_audit_trail(api_client):
    created_study = TestUtils.create_study()

    response = api_client.patch(
        f"/studies/{created_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Study-fields audit trail for all sections
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    for audit_trail_item in res:
        actions = audit_trail_item["actions"]
        for action in actions:
            assert action["section"] in [
                "study_description",
                "Unknown",
                "identification_metadata",
            ]

    # Study-fields audit trail for all sections without identification_metadata
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
        params={"exclude_sections": ["identification_metadata"]},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    for audit_trail_item in res:
        actions = audit_trail_item["actions"]
        for action in actions:
            # we have filtered out the identification_metadata entries, so we should only have
            # study_description entry for study_title patch and Unknown section for preferred_time_unit that is not
            # included in any Study sections
            assert action["section"] in ["study_description", "Unknown"]

    # Study-fields audit trail with non-existent section sent
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
        params={"exclude_sections": ["non-existent section"]},
    )
    assert_response_status_code(response, 400)

    response = api_client.patch(
        f"/studies/{created_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": None}}},
    )
    assert_response_status_code(response, 200)

    # Study-fields audit trail for all sections
    response = api_client.get(
        f"/studies/{created_study.uid}/fields-audit-trail",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res[0]["actions"][0]["action"] == "Delete"
    assert res[0]["actions"][0]["after_value"]


def test_patch_study(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {"study_acronym": "new acronym"}
            }
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "new acronym"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )


def test_study_delete_successful(api_client):
    study_to_delete = TestUtils.create_study()
    response = api_client.delete(f"/studies/{study_to_delete.uid}")
    assert_response_status_code(response, 204)

    response = api_client.get("/studies", params={"deleted": True})
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["uid"] == study_to_delete.uid

    response = api_client.get("/studies/list", params={"deleted": True})
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1
    assert res[0]["uid"] == study_to_delete.uid

    # try to update the deleted study
    response = api_client.patch(
        f"/studies/{study_to_delete.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study_to_delete.uid}' is deleted."


def test_study_listing(api_client):
    # Create three new studies
    studies = [
        TestUtils.create_study(),
        TestUtils.create_study(),
        TestUtils.create_study(),
    ]

    response = api_client.get("/studies")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) >= 3
    uids = [s["uid"] for s in res["items"]]
    for study in res["items"]:
        assert "current_metadata" in study
        metadata = study["current_metadata"]
        # Check that the expected fields exist
        assert "identification_metadata" in metadata
        assert "version_metadata" in metadata
        # Check that no unwanted field is present
        assert "study_description" in metadata
        assert "high_level_study_design" not in metadata
        assert "study_population" not in metadata
        assert "study_intervention" not in metadata

    for study in studies:
        # Check that each study occurs only once in the list
        assert uids.count(study.uid) == 1


def test_get_default_time_unit(api_client):
    test_study = TestUtils.create_study()
    response = api_client.get(f"/studies/{test_study.uid}/time-units")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_uid"] == test_study.uid
    assert res["time_unit_uid"] == day_unit_definition.uid
    assert res["time_unit_name"] == day_unit_definition.name


def test_edit_time_units(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/time-units",
        json={"unit_definition_uid": day_unit_definition.uid},
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"The Preferred Time Unit for the Study with UID '{study.uid}' is already '{day_unit_definition.uid}'."
    )

    response = api_client.patch(
        f"/studies/{study.uid}/time-units",
        json={"unit_definition_uid": week_unit_definition.uid},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_uid"] == study.uid
    assert res["time_unit_uid"] == week_unit_definition.uid
    assert res["time_unit_name"] == week_unit_definition.name


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
def test_get_studies_csv_xml_excel(api_client, export_format):
    TestUtils.verify_exported_data_format(api_client, export_format, "/studies")


def test_get_specific_version(api_client):
    study = TestUtils.create_study()

    title_1 = "new title"
    title_11 = "title after 1st lock."
    title_12 = "title after 1st release."
    title_2 = "title after 2nd release."
    title_draft = "title after 2nd lock."

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_1}}},
    )
    assert_response_status_code(response, 200)

    TestUtils.set_study_standard_version(study_uid=study.uid)

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

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_11}}},
    )
    assert_response_status_code(response, 200)

    # Release
    response = api_client.post(
        f"/studies/{study.uid}/release",
        json={
            "change_description": "Explicit release",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_12}}},
    )
    assert_response_status_code(response, 200)

    # 2nd Release
    response = api_client.post(
        f"/studies/{study.uid}/release",
        json={
            "change_description": "Explicit second release",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_2}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "Lock 2",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

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

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_draft}}},
    )
    assert_response_status_code(response, 200)

    # check study title in different versions
    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"], "study_value_version": "1"},
    )
    res = response.json()
    res_title = res["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_1
    assert res["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"

    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["study_description"],
            "study_value_version": "1.1",
        },
    )
    res = response.json()
    res_title = res["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_11
    assert res["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"

    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["study_description"],
            "study_value_version": "1.2",
        },
    )
    res = response.json()
    res_title = res["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_12
    assert res["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"

    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"], "study_value_version": "2"},
    )
    res = response.json()
    res_title = res["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_2
    assert res["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"

    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"]},
    )
    res = response.json()
    res_title = res["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_draft
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"


def test_get_protocol_title_for_specific_version(api_client):
    study = TestUtils.create_study()
    TestUtils.create_library(name="UCUM", is_editable=True)
    codelist = TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)
    library_name = "Sponsor"
    catalogue_name = "SDTM CT"

    # Create CT Terms

    ct_term_dosage = create_ct_term(
        "dosage_form_1",
        "dosage_form_1",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": "C66726",
                "order": 1,
                "submission_value": "Dosage Form 1",
            }
        ],
    )

    ct_term_delivery_device = create_ct_term(
        "delivery_device_1",
        "delivery_device_1",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": CT_CODELIST_UIDS.delivery_device,
                "order": 1,
                "submission_value": "DD 1",
            }
        ],
    )

    ct_term_dose_frequency = create_ct_term(
        "dose_frequency_1",
        "dose_frequency_1",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": CT_CODELIST_UIDS.frequency,
                "order": 1,
                "submission_value": "Freq 1",
            }
        ],
    )

    ct_term_dispenser = create_ct_term(
        "dispenser_1",
        "dispenser_1",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": CT_CODELIST_UIDS.dispenser,
                "order": 1,
                "submission_value": "Disp 1",
            }
        ],
    )

    ct_term_roa = create_ct_term(
        "route_of_administration_1",
        "route_of_administration_1",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": CT_CODELIST_UIDS.roa,
                "order": 1,
                "submission_value": "ROA 1",
            }
        ],
    )

    # Create Numeric values with unit
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")

    compound = TestUtils.create_compound(name="name-AAA", approve=True)
    compound_alias = TestUtils.create_compound_alias(
        name="compAlias-AAA", compound_uid=compound.uid, approve=True
    )
    compound2 = TestUtils.create_compound(name="name-BBB", approve=True)
    compound_alias2 = TestUtils.create_compound_alias(
        name="compAlias-BBB", compound_uid=compound2.uid, approve=True
    )
    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    type_of_trt_codelist = create_codelist(
        name="Type of Treatment",
        uid="CTCodelist_00999",
        catalogue=catalogue_name,
        library=library_name,
        submission_value=settings.type_of_treatment_cl_submval,
    )
    type_of_treatment = create_ct_term(
        name="Investigational Product",
        uid="type_of_treatment_00001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": type_of_trt_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Investigational Product",
            }
        ],
    )

    pharmaceutical_product1 = TestUtils.create_pharmaceutical_product(
        external_id="external_id1",
        dosage_form_uids=[ct_term_dosage.uid],
        route_of_administration_uids=[ct_term_roa.uid],
        formulations=[],
        approve=True,
    )
    medicinal_product1 = TestUtils.create_medicinal_product(
        name="medicinal_product1",
        external_id="external_id1",
        dose_value_uids=[dose_value.uid],
        dose_frequency_uids=[ct_term_dose_frequency.uid],
        delivery_device_uid=ct_term_delivery_device.uid,
        dispenser_uid=ct_term_dispenser.uid,
        pharmaceutical_product_uids=[pharmaceutical_product1.uid],
        compound_uid=compound.uid,
        approve=True,
    )

    # add some metadata to study
    input_metadata_in_study(study.uid)

    # add a study compound
    response = api_client.post(
        f"/studies/{study.uid}/study-compounds",
        json={
            "compound_alias_uid": compound_alias.uid,
            "medicinal_product_uid": medicinal_product1.uid,
            "type_of_treatment_uid": type_of_treatment.uid,
        },
    )
    res = response.json()
    study_compound_uid = res["study_compound_uid"]
    assert_response_status_code(response, 201)

    TestUtils.set_study_standard_version(study_uid=study.uid)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
            "protocol_header_major_version": 1,
            "protocol_header_minor_version": 0,
        },
    )
    assert_response_status_code(response, 201)

    # Get protocol-title just after locking to save protocol header verstion
    response = api_client.get(
        f"/studies/{study.uid}/protocol-title",
    )
    assert_response_status_code(response, 200)
    res_old = response.json()

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

    # Update
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "study_description": {
                    "study_title": "some title, updated",
                }
            }
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {
                    "registry_identifiers": {"eudract_id": "eudract_id, updated"}
                },
            }
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.patch(
        f"/studies/{study.uid}/study-compounds/{study_compound_uid}",
        json={"compound_alias_uid": compound_alias2.uid},
    )
    assert_response_status_code(response, 200)
    # check the study compound dosings for version 1 is same as first locked
    res_new = api_client.get(
        f"/studies/{study.uid}/protocol-title",
    ).json()
    res_v1 = api_client.get(
        f"/studies/{study.uid}/protocol-title?study_value_version=1",
    ).json()
    assert res_v1 == res_old
    assert res_v1 != res_new
    assert res_new["protocol_header_version"] == "1.0"
    assert res_v1["protocol_header_version"] == "1.0"
    assert res_old["protocol_header_version"] == "1.0"


def test_create_study_subpart(api_client):
    response = api_client.post(
        "/studies",
        json={
            "study_subpart_acronym": "SUB1",
            "description": "desc",
            "study_parent_part_uid": study.uid,
        },
    )
    assert_response_status_code(response, 201)
    post_res = response.json()
    assert post_res["uid"]
    assert post_res["study_parent_part"] == {
        "uid": "Study_000002",
        "study_number": study.current_metadata.identification_metadata.study_number,
        "study_acronym": "new acronym",
        "project_number": "123",
        "description": study.current_metadata.identification_metadata.description,
        "study_id": study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert post_res["study_subpart_uids"] == []
    assert post_res["current_metadata"].get("identification_metadata") == {
        "study_number": study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "study_acronym": "new acronym",
        "study_subpart_acronym": "SUB1",
        "project_number": "123",
        "project_name": "Project ABC",
        "description": "desc",
        "clinical_programme_name": test_data_dict["clinical_programme"].name,
        "study_id": f"{study.current_metadata.identification_metadata.study_id}-SUB1",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert post_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert post_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        post_res["current_metadata"]["version_metadata"]["version_author"]
        == AUTHOR_USERNAME
    )
    assert (
        post_res["current_metadata"]["version_metadata"]["version_description"] is None
    )

    # Check get response of study subpart
    response = api_client.get(f"/studies/{post_res['uid']}")
    assert_response_status_code(response, 200)
    get_res = response.json()
    assert get_res["uid"] == post_res["uid"]
    assert get_res["study_parent_part"] == {
        "uid": "Study_000002",
        "study_number": study.current_metadata.identification_metadata.study_number,
        "study_acronym": "new acronym",
        "project_number": "123",
        "description": study.current_metadata.identification_metadata.description,
        "study_id": study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert get_res["study_subpart_uids"] == []
    assert get_res["current_metadata"].get("identification_metadata") == {
        "study_number": study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "study_acronym": "new acronym",
        "study_subpart_acronym": "SUB1",
        "project_number": "123",
        "project_name": "Project ABC",
        "description": "desc",
        "clinical_programme_name": test_data_dict["clinical_programme"].name,
        "study_id": f"{study.current_metadata.identification_metadata.study_id}-SUB1",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert get_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert get_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        get_res["current_metadata"]["version_metadata"]["version_author"]
        == AUTHOR_USERNAME
    )
    assert (
        get_res["current_metadata"]["version_metadata"]["version_description"] is None
    )

    # Check get response of study parent part
    response = api_client.get(f"/studies/{study.uid}")
    assert_response_status_code(response, 200)
    get_res = response.json()
    assert get_res["uid"] == study.uid
    assert get_res["study_parent_part"] is None
    assert get_res["study_subpart_uids"] == [post_res["uid"]]
    assert get_res["current_metadata"]["identification_metadata"] is not None
    assert get_res["current_metadata"]["version_metadata"] is not None
    assert get_res["current_metadata"].get("high_level_study_design") is None
    assert get_res["current_metadata"].get("study_population") is None
    assert get_res["current_metadata"].get("study_intervention") is None
    assert get_res["current_metadata"].get("study_description") is not None


def test_use_an_already_existing_study_as_a_study_subpart(api_client):
    parent_study = TestUtils.create_study()
    new_study = TestUtils.create_study()
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": parent_study.uid,
            "current_metadata": {
                "identification_metadata": {
                    "study_acronym": "something",
                    "study_subpart_acronym": "SUB1",
                }
            },
        },
    )
    assert_response_status_code(response, 200)
    post_res = response.json()
    assert post_res["uid"]
    assert post_res["study_parent_part"] == {
        "uid": parent_study.uid,
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "project_number": "123",
        "description": parent_study.current_metadata.identification_metadata.description,
        "study_id": parent_study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert post_res["study_subpart_uids"] == []
    assert post_res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "study_subpart_acronym": "SUB1",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": new_study.current_metadata.identification_metadata.description,
        "clinical_programme_name": test_data_dict["clinical_programme"].name,
        "study_id": f"{parent_study.current_metadata.identification_metadata.study_id}-SUB1",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert post_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert post_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        post_res["current_metadata"]["version_metadata"]["version_author"]
        == AUTHOR_USERNAME
    )
    assert (
        post_res["current_metadata"]["version_metadata"]["version_description"] is None
    )

    # Check get response of study parent part
    response = api_client.get(f"/studies/{parent_study.uid}")
    assert_response_status_code(response, 200)
    get_res = response.json()
    assert get_res["uid"] == parent_study.uid
    assert get_res["study_parent_part"] is None
    assert get_res["study_subpart_uids"] == [post_res["uid"]]
    assert get_res["current_metadata"]["identification_metadata"] is not None
    assert get_res["current_metadata"]["version_metadata"] is not None
    assert get_res["current_metadata"].get("high_level_study_design") is None
    assert get_res["current_metadata"].get("study_population") is None
    assert get_res["current_metadata"].get("study_intervention") is None
    assert get_res["current_metadata"].get("study_description") is not None

    # Check get response of study subpart
    response = api_client.get(f"/studies/{new_study.uid}")
    assert_response_status_code(response, 200)
    get_res = response.json()
    assert get_res["study_parent_part"] == {
        "uid": parent_study.uid,
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "project_number": "123",
        "description": parent_study.current_metadata.identification_metadata.description,
        "study_id": parent_study.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert get_res["study_subpart_uids"] == []
    assert get_res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "study_subpart_acronym": "SUB1",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": new_study.current_metadata.identification_metadata.description,
        "clinical_programme_name": test_data_dict["clinical_programme"].name,
        "study_id": f"{parent_study.current_metadata.identification_metadata.study_id}-SUB1",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert get_res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert get_res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        get_res["current_metadata"]["version_metadata"]["version_author"]
        == AUTHOR_USERNAME
    )
    assert (
        get_res["current_metadata"]["version_metadata"]["version_description"] is None
    )


def test_cascade_of_study_parent_part(api_client):
    def _check_study_subparts_status(status: str):
        response = api_client.get(
            "/studies",
            params={
                "filters": json.dumps(
                    {
                        "study_parent_part.uid": {
                            "v": [f"{parent_study.uid}"],
                            "op": "eq",
                        }
                    }
                ),
                "page_size": 0,
            },
        )
        assert_response_status_code(response, 200)
        res = response.json()
        for item in res["items"]:
            assert (
                item["current_metadata"]["version_metadata"]["study_status"] == status
            )

    parent_study = TestUtils.create_study()
    for _ in range(10):
        TestUtils.create_study(study_parent_part_uid=parent_study.uid)

    response = api_client.patch(
        f"/studies/{parent_study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {
                    "registry_identifiers": {
                        "ct_gov_id": "ct_gov_id",
                        "eudract_id": "eudract_id",
                        "investigational_new_drug_application_number_ind": "investigational_new_drug_application_number_ind",
                        "japanese_trial_registry_id_japic": "japanese_trial_registry_id_japic",
                        "universal_trial_number_utn": "universal_trial_number_utn",
                        "eu_trial_number": "eu_trial_number",
                        "civ_id_sin_number": "civ_id_sin_number",
                        "national_clinical_trial_number": "national_clinical_trial_number",
                        "japanese_trial_registry_number_jrct": "japanese_trial_registry_number_jrct",
                        "national_medical_products_administration_nmpa_number": "national_medical_products_administration_nmpa_number",
                        "eudamed_srn_number": "eudamed_srn_number",
                        "investigational_device_exemption_ide_number": "investigational_device_exemption_ide_number",
                        "eu_pas_number": "eu_pas_number",
                    }
                },
                "study_description": {
                    "study_title": "new title",
                    "study_short_title": "new short title",
                },
            }
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        "/studies",
        params={
            "filters": json.dumps(
                {
                    "study_parent_part.uid": {
                        "v": [f"{parent_study.uid}"],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    for item in res["items"]:
        response = api_client.get(f"/studies/{item['uid']}")
        rs = response.json()
        assert rs["current_metadata"]["study_description"]["study_title"] == "new title"
        assert (
            rs["current_metadata"]["study_description"]["study_short_title"]
            == "new short title"
        )
        assert rs["current_metadata"]["identification_metadata"][
            "registry_identifiers"
        ] == {
            "ct_gov_id": "ct_gov_id",
            "ct_gov_id_null_value_code": None,
            "eudract_id": "eudract_id",
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": "investigational_new_drug_application_number_ind",
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": "japanese_trial_registry_id_japic",
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": "universal_trial_number_utn",
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": "eu_trial_number",
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": "civ_id_sin_number",
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": "national_clinical_trial_number",
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": "japanese_trial_registry_number_jrct",
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": "national_medical_products_administration_nmpa_number",
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": "eudamed_srn_number",
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": "investigational_device_exemption_ide_number",
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": "eu_pas_number",
            "eu_pas_number_null_value_code": None,
        }

    TestUtils.set_study_standard_version(study_uid=parent_study.uid)

    response = api_client.post(
        f"/studies/{parent_study.uid}/locks",
        json={
            "change_description": "Locked",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"
    _check_study_subparts_status("LOCKED")

    response = api_client.post(
        f"/studies/{parent_study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    _check_study_subparts_status("DRAFT")

    response = api_client.post(
        f"/studies/{parent_study.uid}/release",
        json={
            "change_description": "Released",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    _check_study_subparts_status("DRAFT")


def test_reordering_study_subparts(api_client):
    global study_with_subparts
    global subpart_studies
    parent_study = TestUtils.create_study()
    study_with_subparts = parent_study
    new_studies = [
        TestUtils.create_study(study_parent_part_uid=parent_study.uid)
        for _ in range(10)
    ]
    subpart_studies = new_studies

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[2].uid,
            "subpart_id": "a",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "a"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "j"

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[5].uid,
            "subpart_id": "d",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "a"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "j"

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[9].uid,
            "subpart_id": "a",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "j"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "a"

    response = api_client.patch(
        f"/studies/{parent_study.uid}/order",
        json={
            "uid": new_studies[9].uid,
            "subpart_id": "j",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] == "b"
    assert res[1]["current_metadata"]["identification_metadata"]["subpart_id"] == "c"
    assert res[2]["current_metadata"]["identification_metadata"]["subpart_id"] == "a"
    assert res[3]["current_metadata"]["identification_metadata"]["subpart_id"] == "e"
    assert res[4]["current_metadata"]["identification_metadata"]["subpart_id"] == "f"
    assert res[5]["current_metadata"]["identification_metadata"]["subpart_id"] == "d"
    assert res[6]["current_metadata"]["identification_metadata"]["subpart_id"] == "g"
    assert res[7]["current_metadata"]["identification_metadata"]["subpart_id"] == "h"
    assert res[8]["current_metadata"]["identification_metadata"]["subpart_id"] == "i"
    assert res[9]["current_metadata"]["identification_metadata"]["subpart_id"] == "j"
    new_studies[0].current_metadata.identification_metadata.subpart_id = "b"
    new_studies[1].current_metadata.identification_metadata.subpart_id = "c"
    new_studies[2].current_metadata.identification_metadata.subpart_id = "a"
    new_studies[3].current_metadata.identification_metadata.subpart_id = "e"
    new_studies[4].current_metadata.identification_metadata.subpart_id = "f"
    new_studies[5].current_metadata.identification_metadata.subpart_id = "d"
    new_studies[6].current_metadata.identification_metadata.subpart_id = "g"
    new_studies[7].current_metadata.identification_metadata.subpart_id = "h"
    new_studies[8].current_metadata.identification_metadata.subpart_id = "i"
    new_studies[9].current_metadata.identification_metadata.subpart_id = "j"


def test_auto_reordering_after_deleting_a_study_subpart(api_client):
    parent_study = TestUtils.create_study()
    new_studies = [
        TestUtils.create_study(study_parent_part_uid=parent_study.uid)
        for _ in range(10)
    ]

    uids_of_random_study_subparts_to_delete = {
        random_study.uid
        for random_study in random.choices(new_studies, k=random.randint(0, 7))
    }
    for (
        uid_of_random_study_subpart_to_delete
    ) in uids_of_random_study_subparts_to_delete:
        response = api_client.delete(
            f"/studies/{uid_of_random_study_subpart_to_delete}"
        )
        assert_response_status_code(response, 204)

    response = api_client.get(
        "/studies",
        params={
            "filters": json.dumps(
                {
                    "study_parent_part.uid": {
                        "v": [f"{parent_study.uid}"],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()

    letters = ascii_lowercase[: 10 - len(uids_of_random_study_subparts_to_delete)]
    idx = 0
    for item in res["items"]:
        if item["uid"] not in uids_of_random_study_subparts_to_delete:
            assert (
                item["current_metadata"]["identification_metadata"]["subpart_id"]
                == letters[idx]
            )
            idx += 1

    study_uids = [item["uid"] for item in res["items"]]
    assert all(
        uid_of_random_study_subpart_to_delete not in study_uids
        for uid_of_random_study_subpart_to_delete in uids_of_random_study_subparts_to_delete
    )


def test_remove_study_subpart_from_parent_part(api_client):
    parent_part = TestUtils.create_study()
    new_study = StudyService().create(
        StudyCreateInput(
            study_number="8772",
            study_acronym=None,
            project_number=PROJECT_NUMBER,
            description=None,
        )
    )
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {
                "identification_metadata": {
                    "study_subpart_acronym": "SUB1",
                }
            },
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"]
    assert res["study_parent_part"] == {
        "uid": parent_part.uid,
        "study_number": parent_part.current_metadata.identification_metadata.study_number,
        "study_acronym": parent_part.current_metadata.identification_metadata.study_acronym,
        "project_number": "123",
        "description": parent_part.current_metadata.identification_metadata.description,
        "study_id": parent_part.current_metadata.identification_metadata.study_id,
        "study_title": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_part.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": parent_part.current_metadata.identification_metadata.study_acronym,
        "study_subpart_acronym": "SUB1",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": None,
        "clinical_programme_name": test_data_dict["clinical_programme"].name,
        "study_id": f"{parent_part.current_metadata.identification_metadata.study_id}-SUB1",
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        res["current_metadata"]["version_metadata"]["version_author"] == AUTHOR_USERNAME
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None

    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {
                "identification_metadata": {"study_acronym": "something"}
            },
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"].get("identification_metadata") == {
        "study_number": None,
        "subpart_id": None,
        "project_number": "123",
        "study_acronym": "something",
        "study_subpart_acronym": None,
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": None,
        "clinical_programme_name": test_data_dict["clinical_programme"].name,
        "study_id": None,
        "registry_identifiers": {
            "ct_gov_id": None,
            "ct_gov_id_null_value_code": None,
            "eudract_id": None,
            "eudract_id_null_value_code": None,
            "investigational_new_drug_application_number_ind": None,
            "investigational_new_drug_application_number_ind_null_value_code": None,
            "japanese_trial_registry_id_japic": None,
            "japanese_trial_registry_id_japic_null_value_code": None,
            "universal_trial_number_utn": None,
            "universal_trial_number_utn_null_value_code": None,
            "eu_trial_number": None,
            "eu_trial_number_null_value_code": None,
            "civ_id_sin_number": None,
            "civ_id_sin_number_null_value_code": None,
            "national_clinical_trial_number": None,
            "national_clinical_trial_number_null_value_code": None,
            "japanese_trial_registry_number_jrct": None,
            "japanese_trial_registry_number_jrct_null_value_code": None,
            "national_medical_products_administration_nmpa_number": None,
            "national_medical_products_administration_nmpa_number_null_value_code": None,
            "eudamed_srn_number": None,
            "eudamed_srn_number_null_value_code": None,
            "investigational_device_exemption_ide_number": None,
            "investigational_device_exemption_ide_number_null_value_code": None,
            "eu_pas_number": None,
            "eu_pas_number_null_value_code": None,
        },
    }
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        res["current_metadata"]["version_metadata"]["version_author"] == AUTHOR_USERNAME
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None


def test_detach_study_subpart_minimal_identification_preserves_standalone_acronym(
    api_client,
):
    """UI-style detach sends only ``study_number: null``; acronym must survive merge + detach."""
    parent_part = TestUtils.create_study(acronym="MCPDETP1")
    new_study = StudyService().create(
        StudyCreateInput(
            study_number="5551",
            study_acronym="MCPDETS1",
            project_number=PROJECT_NUMBER,
            description=None,
        )
    )
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {
                "identification_metadata": {
                    "study_subpart_acronym": "MCPDETSP",
                }
            },
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {
                "identification_metadata": {
                    "study_number": None,
                }
            },
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_parent_part"] is None
    id_meta = res["current_metadata"]["identification_metadata"]
    assert id_meta["study_subpart_acronym"] is None
    assert id_meta["study_number"] is None
    assert id_meta["study_acronym"] == "MCPDETP1"


def test_detach_study_subpart_requires_identification_section(api_client):
    parent_part = TestUtils.create_study(acronym="MCPDETP2")
    subpart = TestUtils.create_study(study_parent_part_uid=parent_part.uid)
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={"study_parent_part_uid": None},
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["type"] == "BusinessLogicException"
    assert "identification is required" in res["message"]


# pylint: disable=too-many-statements
def test_get_audit_trail_of_all_study_subparts_of_study(api_client):
    response = api_client.get(
        f"/studies/{study_with_subparts.uid}/audit-trail?page_size=0"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    items = res["items"]
    for i in [
        "subpart_uid",
        "subpart_id",
        "study_acronym",
        "study_subpart_acronym",
        "start_date",
        "end_date",
        "change_type",
        "changes",
    ]:
        assert i in items[0]

    assert len(items) == 36

    assert items[0]["subpart_id"] == "i"
    assert items[0]["subpart_uid"] == "Study_000034"
    assert items[1]["subpart_id"] == "h"
    assert items[1]["subpart_uid"] == "Study_000033"
    assert items[2]["subpart_id"] == "g"
    assert items[2]["subpart_uid"] == "Study_000032"
    assert items[3]["subpart_id"] == "f"
    assert items[3]["subpart_uid"] == "Study_000030"
    assert items[4]["subpart_id"] == "e"
    assert items[4]["subpart_uid"] == "Study_000029"
    assert items[5]["subpart_id"] == "d"
    assert items[5]["subpart_uid"] == "Study_000031"
    assert items[6]["subpart_id"] == "c"
    assert items[6]["subpart_uid"] == "Study_000027"
    assert items[7]["subpart_id"] == "b"
    assert items[7]["subpart_uid"] == "Study_000026"
    assert items[8]["subpart_id"] == "a"
    assert items[8]["subpart_uid"] == "Study_000028"
    assert items[9]["subpart_id"] == "j"
    assert items[9]["subpart_uid"] == "Study_000035"
    assert items[10]["subpart_id"] == "a"
    assert items[10]["subpart_uid"] == "Study_000035"
    assert items[11]["subpart_id"] == "j"
    assert items[11]["subpart_uid"] == "Study_000034"
    assert items[12]["subpart_id"] == "i"
    assert items[12]["subpart_uid"] == "Study_000033"
    assert items[13]["subpart_id"] == "h"
    assert items[13]["subpart_uid"] == "Study_000032"
    assert items[14]["subpart_id"] == "g"
    assert items[14]["subpart_uid"] == "Study_000030"
    assert items[15]["subpart_id"] == "f"
    assert items[15]["subpart_uid"] == "Study_000029"
    assert items[16]["subpart_id"] == "e"
    assert items[16]["subpart_uid"] == "Study_000031"
    assert items[17]["subpart_id"] == "d"
    assert items[17]["subpart_uid"] == "Study_000027"
    assert items[18]["subpart_id"] == "c"
    assert items[18]["subpart_uid"] == "Study_000026"
    assert items[19]["subpart_id"] == "b"
    assert items[19]["subpart_uid"] == "Study_000028"
    assert items[20]["subpart_id"] == "d"
    assert items[20]["subpart_uid"] == "Study_000031"
    assert items[21]["subpart_id"] == "f"
    assert items[21]["subpart_uid"] == "Study_000030"
    assert items[22]["subpart_id"] == "e"
    assert items[22]["subpart_uid"] == "Study_000029"
    assert items[23]["subpart_id"] == "a"
    assert items[23]["subpart_uid"] == "Study_000028"
    assert items[24]["subpart_id"] == "c"
    assert items[24]["subpart_uid"] == "Study_000027"
    assert items[25]["subpart_id"] == "b"
    assert items[25]["subpart_uid"] == "Study_000026"
    assert items[26]["subpart_id"] == "j"
    assert items[26]["subpart_uid"] == "Study_000035"
    assert items[27]["subpart_id"] == "i"
    assert items[27]["subpart_uid"] == "Study_000034"
    assert items[28]["subpart_id"] == "h"
    assert items[28]["subpart_uid"] == "Study_000033"
    assert items[29]["subpart_id"] == "g"
    assert items[29]["subpart_uid"] == "Study_000032"
    assert items[30]["subpart_id"] == "f"
    assert items[30]["subpart_uid"] == "Study_000031"
    assert items[31]["subpart_id"] == "e"
    assert items[31]["subpart_uid"] == "Study_000030"
    assert items[32]["subpart_id"] == "d"
    assert items[32]["subpart_uid"] == "Study_000029"
    assert items[33]["subpart_id"] == "c"
    assert items[33]["subpart_uid"] == "Study_000028"
    assert items[34]["subpart_id"] == "b"
    assert items[34]["subpart_uid"] == "Study_000027"
    assert items[35]["subpart_id"] == "a"
    assert items[35]["subpart_uid"] == "Study_000026"

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_with_subparts.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    TestUtils.set_study_standard_version(study_uid=study_with_subparts.uid)

    # Lock
    response = api_client.post(
        f"/studies/{study_with_subparts.uid}/locks",
        json={
            "change_description": "version Lock",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Unlock
    response = api_client.post(
        f"/studies/{study_with_subparts.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.patch(
        "/studies/Study_000026",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {
                "identification_metadata": {
                    "study_number": None,
                }
            },
        },
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study_with_subparts.uid}/locks",
        json={
            "change_description": "version Lock",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Unlock
    response = api_client.post(
        f"/studies/{study_with_subparts.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{study_with_subparts.uid}/audit-trail?study_value_version=1&page_size=0"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert all(
        i["end_date"] for i in res["items"] if i["subpart_uid"] == "Study_000026"
    )


def test_get_audit_trail_of_study_subpart(api_client):
    response = api_client.get(
        "/studies/Study_000030/audit-trail?is_subpart=true&page_size=0"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    items = res["items"]
    for i in [
        "subpart_uid",
        "subpart_id",
        "study_acronym",
        "study_subpart_acronym",
        "start_date",
        "end_date",
        "change_type",
        "changes",
    ]:
        assert i in items[0]

    assert len(items) == 11

    assert items[0]["subpart_id"] == "e"
    assert items[0]["subpart_uid"] == "Study_000030"
    assert items[1]["subpart_id"] == "e"
    assert items[1]["subpart_uid"] == "Study_000030"
    assert items[2]["subpart_id"] == "e"
    assert items[2]["subpart_uid"] == "Study_000030"
    assert items[3]["subpart_id"] == "e"
    assert items[3]["subpart_uid"] == "Study_000030"
    assert items[4]["subpart_id"] == "f"
    assert items[4]["subpart_uid"] == "Study_000030"
    assert items[5]["subpart_id"] == "f"
    assert items[5]["subpart_uid"] == "Study_000030"
    assert items[6]["subpart_id"] == "f"
    assert items[6]["subpart_uid"] == "Study_000030"
    assert items[7]["subpart_id"] == "f"
    assert items[7]["subpart_uid"] == "Study_000030"
    assert items[8]["subpart_id"] == "g"
    assert items[8]["subpart_uid"] == "Study_000030"
    assert items[9]["subpart_id"] == "f"
    assert items[9]["subpart_uid"] == "Study_000030"
    assert items[10]["subpart_id"] == "e"
    assert items[10]["subpart_uid"] == "Study_000030"


def test_cannot_use_a_study_parent_part_as_study_subpart(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "study_parent_part_uid": "Study_000001",
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Cannot use Study Parent Part with UID '{study.uid}' as a Study Subpart."
    )


def test_cannot_add_a_study_subpart_without_study_subpart_acronym(
    api_client,
):
    subpart = TestUtils.create_study()
    parent_part = TestUtils.create_study()
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "ValidationException"
    assert res["message"] == "Study Subpart Acronym must be provided for Study Subpart."


def test_cannot_use_a_study_subpart_with_different_project_number_than_study_parent_part(
    api_client,
):
    subpart = TestUtils.create_study()
    project = TestUtils.create_project(
        project_number="0000", clinical_programme_uid="ClinicalProgramme_000001"
    )
    parent_part = TestUtils.create_study(project_number=project.project_number)
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Project number of Study Parent Part and Study Subpart must be same."
    )


def test_cannot_use_a_study_subpart_as_study_parent_part(api_client):
    subpart = TestUtils.create_study(study_parent_part_uid=study.uid)
    local_study = TestUtils.create_study()
    response = api_client.patch(
        f"/studies/{local_study.uid}",
        json={
            "study_parent_part_uid": subpart.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Provided study_parent_part_uid '{subpart.uid}' is a Study Subpart UID."
    )


def test_cannot_make_a_study_a_subpart_of_itself(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "study_parent_part_uid": study.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "A Study cannot be a Study Parent Part for itself."


def test_cannot_reorder_study_subpart_of_another_study_parent_part(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/order",
        json={
            "uid": "Study_000006",
            "subpart_id": "a",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Study Subparts with UID 'Study_000006' don't belong to the Study Parent Part with UID '{study.uid}'."
    )


def test_cannot_delete_study_parent_part(api_client):
    TestUtils.create_study(study_parent_part_uid=study.uid)
    TestUtils.create_study(study_parent_part_uid=study.uid)

    study_response = api_client.get(f"/studies/{study.uid}")
    assert_response_status_code(study_response, 200)
    expected_subparts = study_response.json()["study_subpart_uids"]

    response = api_client.delete(f"/studies/{study.uid}")
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Study {study.uid}: cannot delete a Study having Study Subparts: {expected_subparts}."
    )


def test_cannot_change_study_title_of_subpart(api_client):
    subpart = TestUtils.create_study(study_parent_part_uid=study.uid)
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": "Study_000002",
            "current_metadata": {
                "study_description": {
                    "title": "new title",
                }
            },
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot add or edit Study Description of Study Subparts."


def test_cannot_change_registry_identifiers_of_subpart(api_client):
    subpart = TestUtils.create_study(study_parent_part_uid=study.uid)
    response = api_client.patch(
        f"/studies/{subpart.uid}",
        json={
            "study_parent_part_uid": "Study_000002",
            "current_metadata": {
                "identification_metadata": {
                    "registry_identifiers": {"eudract_id": "eudract_id, updated"}
                }
            },
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot edit Registry Identifiers of Study Subparts."


def test_cannot_change_project_of_subpart(api_client):
    new_project = TestUtils.create_project(
        name="New Project",
        project_number="abcd",
        clinical_programme_uid="ClinicalProgramme_000001",
    )
    response = api_client.patch(
        "/studies/Study_000011",
        json={
            "study_parent_part_uid": "Study_000002",
            "current_metadata": {
                "identification_metadata": {
                    "project_number": new_project.project_number,
                }
            },
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Project of Study Subparts cannot be changed independently from its Study Parent Part."
    )


def test_cannot_lock_study_subpart(api_client):
    TestUtils.set_study_standard_version(study_uid="Study_000011")

    response = api_client.post(
        "/studies/Study_000011/locks",
        json={
            "change_description": "Lock",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be locked independently from its Study Parent Part with UID 'Study_000002'."
    )


def test_cannot_unlock_study_subpart(api_client):
    response = api_client.post(
        "/studies/Study_000011/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be unlocked independently from its Study Parent Part with UID 'Study_000002'."
    )


def test_cannot_release_study_subpart(api_client):
    response = api_client.post(
        "/studies/Study_000011/release",
        json={
            "change_description": "Lock",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be released independently from its Study Parent Part with UID 'Study_000002'."
    )


def test_cannot_add_study_subpart_to_a_locked_study_parent_part(api_client):
    _study = TestUtils.create_study()
    study_subpart = TestUtils.create_study()

    response = api_client.patch(
        f"/studies/{_study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "a title"}}},
    )
    assert_response_status_code(response, 200)

    TestUtils.set_study_standard_version(study_uid=_study.uid)

    response = api_client.post(
        f"/studies/{_study.uid}/locks",
        json={
            "change_description": "Lock",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.patch(
        f"/studies/{study_subpart.uid}",
        json={
            "study_parent_part_uid": _study.uid,
            "current_metadata": {"identification_metadata": {}},
        },
    )
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Study Parent Part with UID '{_study.uid}' is locked or doesn't exist."
    )


def test_cannot_remove_study_subpart_from_parent_part_and_provide_an_existing_study_number(
    api_client,
):
    parent_part = TestUtils.create_study(number="1111")
    new_study = TestUtils.create_study(number="0101")
    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": parent_part.uid,
            "current_metadata": {
                "identification_metadata": {
                    "study_subpart_acronym": "SUB1",
                }
            },
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.patch(
        f"/studies/{new_study.uid}",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {
                "identification_metadata": {
                    "study_number": "8772",
                }
            },
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "When removing a Study Subpart from its Study Parent Part the Study Number must be set to null."
    )


def test_study_metadata_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    _study = TestUtils.create_study()

    # edit ctterm
    # change name and approve the version
    new_ctterm_name = "new ctterm name"
    response = api_client.post(
        f"/ct/terms/{ct_term_study_standard_test.term_uid}/names/versions",
    )
    res = response.json()
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/ct/terms/{ct_term_study_standard_test.term_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(
        f"/ct/terms/{ct_term_study_standard_test.term_uid}/names/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # get study with ctterm latest
    def payload_creation(
        _study: StudyPatchRequestJsonModel,
        new_name_ctterm: ct_term.SimpleCTTermNameWithConflictFlag,
    ):
        return StudyPatchRequestJsonModel(
            current_metadata=StudyMetadataJsonModel(
                identification_metadata=StudyIdentificationMetadataJsonModel(
                    study_number=_study.current_metadata.identification_metadata.study_number,
                    subpart_id=_study.current_metadata.identification_metadata.subpart_id,
                    study_acronym=_study.current_metadata.identification_metadata.study_acronym,
                    study_subpart_acronym=_study.current_metadata.identification_metadata.study_subpart_acronym,
                    project_number=_study.current_metadata.identification_metadata.project_number,
                    project_name=_study.current_metadata.identification_metadata.project_name,
                    description=_study.current_metadata.identification_metadata.description,
                    clinical_programme_name=_study.current_metadata.identification_metadata.clinical_programme_name,
                    study_id=_study.current_metadata.identification_metadata.study_id,
                    registry_identifiers=RegistryIdentifiersJsonModel(
                        ct_gov_id=None,
                        ct_gov_id_null_value_code=new_name_ctterm,
                        eudract_id=None,
                        eudract_id_null_value_code=new_name_ctterm,
                        universal_trial_number_utn=None,
                        universal_trial_number_utn_null_value_code=new_name_ctterm,
                        japanese_trial_registry_id_japic=None,
                        japanese_trial_registry_id_japic_null_value_code=new_name_ctterm,
                        investigational_new_drug_application_number_ind=None,
                        investigational_new_drug_application_number_ind_null_value_code=new_name_ctterm,
                        eu_trial_number=None,
                        eu_trial_number_null_value_code=new_name_ctterm,
                        civ_id_sin_number=None,
                        civ_id_sin_number_null_value_code=new_name_ctterm,
                        national_clinical_trial_number=None,
                        national_clinical_trial_number_null_value_code=new_name_ctterm,
                        japanese_trial_registry_number_jrct=None,
                        japanese_trial_registry_number_jrct_null_value_code=new_name_ctterm,
                        national_medical_products_administration_nmpa_number=None,
                        national_medical_products_administration_nmpa_number_null_value_code=new_name_ctterm,
                        eudamed_srn_number=None,
                        eudamed_srn_number_null_value_code=new_name_ctterm,
                        investigational_device_exemption_ide_number=None,
                        investigational_device_exemption_ide_number_null_value_code=new_name_ctterm,
                        eu_pas_number=None,
                        eu_pas_number_null_value_code=new_name_ctterm,
                    ),
                )
            )
        )

    new_named_ctterm = ct_term.SimpleCTTermNameWithConflictFlag(
        term_uid=ct_term_study_standard_test.term_uid,
        sponsor_preferred_name=new_ctterm_name,
        queried_effective_date=None,
        date_conflict=False,
    )
    old_named_ctterm = ct_term.SimpleCTTermNameWithConflictFlag(
        term_uid=ct_term_study_standard_test.term_uid,
        sponsor_preferred_name=ct_term_study_standard_test.sponsor_preferred_name,
        queried_effective_date=None,
        date_conflict=False,
    )
    new_named_ctterm_to_compare = copy.deepcopy(new_named_ctterm)
    new_named_ctterm_to_compare.queried_effective_date = mock.ANY
    new_named_study_payload_to_compare = payload_creation(
        _study, new_named_ctterm_to_compare
    )

    old_named_ctterm_to_compare = copy.deepcopy(old_named_ctterm)
    old_named_ctterm_to_compare.queried_effective_date = mock.ANY
    old_named_study_payload_to_compare = payload_creation(
        _study, old_named_ctterm_to_compare
    )

    new_named_study_payload = payload_creation(_study, new_named_ctterm)
    response = api_client.patch(
        f"/studies/{_study.uid}", json=new_named_study_payload.model_dump()
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["identification_metadata"]
        == new_named_study_payload_to_compare.current_metadata.identification_metadata.model_dump()
    )
    assert (
        new_named_study_payload_to_compare.current_metadata.identification_metadata.model_dump()
        != old_named_study_payload_to_compare.current_metadata.identification_metadata.model_dump()
    )

    TestUtils.set_study_standard_version(
        study_uid=_study.uid,
        package_name="SDTM CT 2020-03-27",
        effective_date=datetime.datetime(2020, 3, 27, tzinfo=datetime.timezone.utc),
    )

    # get study with previous ctterm
    response = api_client.get(
        f"/studies/{_study.uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["identification_metadata"]
        == old_named_study_payload_to_compare.current_metadata.identification_metadata.model_dump()
    )
    assert (
        old_named_study_payload_to_compare.current_metadata.identification_metadata.model_dump()
        != new_named_study_payload_to_compare.current_metadata.identification_metadata.model_dump()
    )


def test_study_copy_component(api_client):
    reference_study = TestUtils.create_study()
    relapse_criteria_ref = "Relapse criteria reference study"
    number_of_expected_subjects_ref = 10
    response = api_client.patch(
        f"/studies/{reference_study.uid}",
        json={
            "current_metadata": {
                "study_population": {
                    "relapse_criteria": relapse_criteria_ref,
                    "number_of_expected_subjects": number_of_expected_subjects_ref,
                }
            }
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{reference_study.uid}",
        params={"include_sections": ["study_population"]},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["study_population"]["relapse_criteria"]
        == relapse_criteria_ref
    )
    assert (
        res["current_metadata"]["study_population"]["number_of_expected_subjects"]
        == number_of_expected_subjects_ref
    )

    relapse_criteria_target = "Relapse criteria target"
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "study_population": {"relapse_criteria": relapse_criteria_target}
            }
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.get(
        f"/studies/{study.uid}", params={"include_sections": ["study_population"]}
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["study_population"]["relapse_criteria"]
        == relapse_criteria_target
    )

    response = api_client.get(
        f"/studies/{study.uid}/copy-component",
        params={
            "reference_study_uid": reference_study.uid,
            "component_to_copy": "study_population",
            "overwrite": False,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["study_population"]["relapse_criteria"]
        == relapse_criteria_target
    )
    assert (
        res["current_metadata"]["study_population"]["number_of_expected_subjects"]
        == number_of_expected_subjects_ref
    )

    response = api_client.get(
        f"/studies/{study.uid}/copy-component",
        params={
            "reference_study_uid": reference_study.uid,
            "component_to_copy": "study_population",
            "overwrite": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["study_population"]["relapse_criteria"]
        == relapse_criteria_ref
    )
    assert (
        res["current_metadata"]["study_population"]["number_of_expected_subjects"]
        == number_of_expected_subjects_ref
    )


def test_get_pharma_cm_representation(
    api_client,
):
    acronym = "Test acronym"
    study = TestUtils.create_study(acronym=acronym)
    eduract_id = "2019-123456-42"
    duration_value = 1
    duration_unit = week_unit_definition
    duration_string = f"{duration_value} {duration_unit.name}"
    is_trial_randomised = True
    study_title = "Study official title"
    study_short_title = "Study short title"
    eudract_id_type = "EudraCT Number"
    eudract_description = "EUDRACT ID"
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {
                    "registry_identifiers": {"eudract_id": eduract_id}
                },
                "study_population": {
                    "planned_maximum_age_of_subjects": {
                        "duration_value": duration_value,
                        "duration_unit_code": {"uid": week_unit_definition.uid},
                    }
                },
                "study_intervention": {"is_trial_randomised": is_trial_randomised},
                "study_description": {
                    "study_title": study_title,
                    "study_short_title": study_short_title,
                },
            },
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.get(
        f"/studies/{study.uid}/pharma-cm",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["unique_protocol_identification_number"]
        == study.current_metadata.identification_metadata.study_id
    )
    assert res["brief_title"] == study_short_title
    assert res["official_title"] == study_title
    assert res["acronym"] == acronym
    assert res["secondary_ids"] == [
        {
            "secondary_id": eduract_id,
            "id_type": eudract_id_type,
            "description": eudract_description,
        }
    ]
    assert res["allocation"] == "N/A"
    assert res["maximum_age"] == duration_string
    assert res["inclusion_criteria"] == []
    assert res["exclusion_criteria"] == []
    assert res["outcome_measures"] == []
    assert res["number_of_subjects"] == 0
    assert res["number_of_arms"] == 0
    assert res["study_arms"] == []

    # Create CT Terms
    criteria_cl = TestUtils.create_ct_codelist(
        name="Criteria Type",
        submission_value="CRITRTP",
        codelist_uid="CriteriaTypeCodelistUid",
        catalogue_name="SDTM CT",
        library_name="Sponsor",
        extensible=True,
        approve=True,
    )
    inclusion_criteria_term = "INCLUSION CRITERIA"
    ct_term_inclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name=inclusion_criteria_term,
        sponsor_preferred_name_sentence_case=inclusion_criteria_term.lower(),
        codelist_uid=criteria_cl.codelist_uid,
    )
    exclusion_criteria_term = "EXCLUSION CRITERIA"
    ct_term_exclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name=exclusion_criteria_term,
        sponsor_preferred_name_sentence_case=exclusion_criteria_term.lower(),
        codelist_uid=criteria_cl.codelist_uid,
    )

    # Create criteria templates
    incl_criteria_template_1 = TestUtils.create_criteria_template(
        type_uid=ct_term_inclusion_criteria.term_uid
    )

    excl_criteria_template_1 = TestUtils.create_criteria_template(
        type_uid=ct_term_exclusion_criteria.term_uid
    )

    # Create inclusion study criteria
    inclusion_study_criteria = TestUtils.create_study_criteria(
        study_uid=study.uid,
        criteria_template_uid=incl_criteria_template_1.uid,
        library_name=incl_criteria_template_1.library.name,
        parameter_terms=[],
    )

    # mark inclusion criteria as key criteria
    response = api_client.patch(
        f"/studies/{study.uid}/study-criteria/{inclusion_study_criteria.study_criteria_uid}/key-criteria",
        json={
            "key_criteria": True,
        },
    )
    assert_response_status_code(response, 200)

    TestUtils.create_study_criteria(
        study_uid=study.uid,
        criteria_template_uid=excl_criteria_template_1.uid,
        library_name=excl_criteria_template_1.library.name,
        parameter_terms=[],
    )

    # Create objective template
    objective_template = TestUtils.create_objective_template()
    study_objective = TestUtils.create_study_objective(
        study_uid=study.uid,
        objective_template_uid=objective_template.uid,
        library_name=objective_template.library.name,
        parameter_terms=[],
    )

    endpoint_template = TestUtils.create_endpoint_template()

    unit_separator = "and"
    timeframe_template = TestUtils.create_timeframe_template()
    timeframe = TestUtils.create_timeframe(
        timeframe_template_uid=timeframe_template.uid
    )
    TestUtils.create_template_parameter(settings.study_endpoint_tp_name)

    # Create study endpoints
    TestUtils.create_study_endpoint(
        study_uid=study.uid,
        endpoint_template_uid=endpoint_template.uid,
        endpoint_units=EndpointUnitsInput(
            units=[day_unit_definition.uid, week_unit_definition.uid],
            separator=unit_separator,
        ),
        timeframe_uid=timeframe.uid,
        library_name=endpoint_template.library.name,
        study_objective_uid=study_objective.study_objective_uid,
    )
    response = api_client.get(
        f"/studies/{study.uid}/pharma-cm",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["unique_protocol_identification_number"]
        == study.current_metadata.identification_metadata.study_id
    )
    assert res["brief_title"] == study_short_title
    assert res["official_title"] == study_title
    assert res["acronym"] == acronym
    assert res["secondary_ids"] == [
        {
            "secondary_id": eduract_id,
            "id_type": eudract_id_type,
            "description": eudract_description,
        }
    ]
    assert res["allocation"] == "N/A"
    assert res["maximum_age"] == duration_string
    assert res["inclusion_criteria"] == [incl_criteria_template_1.name_plain]
    assert res["exclusion_criteria"] == []
    assert res["outcome_measures"] == [
        {
            "title": objective_template.name_plain,
            "timeframe": timeframe.name_plain,
            "description": "day and week",
        }
    ]
    assert res["number_of_subjects"] == 0
    assert res["number_of_arms"] == 0
    assert res["study_arms"] == []

    # yes no response codelist
    arm_type_codelist = create_codelist(
        name="Arm Type",
        submission_value="ARMTTP",
        uid="ArmTypeCodelistUid",
        catalogue="SDTM CT",
        library="Sponsor",
    )

    arm_type = "Investigational Arm"
    investigational_arm = TestUtils.create_ct_term(
        sponsor_preferred_name=arm_type,
        sponsor_preferred_name_sentence_case=arm_type.lower(),
        codelist_uid=arm_type_codelist.codelist_uid,
    )
    arm_with_type = TestUtils.create_study_arm(
        study_uid=study.uid,
        arm_type_uid=investigational_arm.term_uid,
        name="Arm 1 name",
        short_name="Arm 1 short name",
        description="Arm 1 description",
        number_of_subjects=10,
    )
    arm_without_type = TestUtils.create_study_arm(
        study_uid=study.uid,
        name="Arm 2 name",
        short_name="Arm 2 short name",
        description="Arm 2 description",
        number_of_subjects=20,
    )
    response = api_client.get(
        f"/studies/{study.uid}/pharma-cm",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["unique_protocol_identification_number"]
        == study.current_metadata.identification_metadata.study_id
    )
    assert res["brief_title"] == study_short_title
    assert res["official_title"] == study_title
    assert res["acronym"] == acronym
    assert res["secondary_ids"] == [
        {
            "secondary_id": eduract_id,
            "id_type": eudract_id_type,
            "description": eudract_description,
        }
    ]
    assert res["allocation"] == "N/A"
    assert res["maximum_age"] == duration_string

    assert res["inclusion_criteria"] == [incl_criteria_template_1.name_plain]
    assert res["exclusion_criteria"] == []
    assert res["outcome_measures"] == [
        {
            "title": objective_template.name_plain,
            "timeframe": timeframe.name_plain,
            "description": "day and week",
        }
    ]
    assert (
        arm_with_type.number_of_subjects
        and arm_without_type.number_of_subjects
        and res["number_of_subjects"]
        == arm_with_type.number_of_subjects + arm_without_type.number_of_subjects
    )
    assert res["number_of_arms"] == 2
    assert res["study_arms"] == [
        {
            "arm_type": investigational_arm.sponsor_preferred_name,
            "arm_title": arm_with_type.name,
            "arm_description": arm_with_type.description,
        },
        {
            "arm_type": None,
            "arm_title": arm_without_type.name,
            "arm_description": arm_without_type.description,
        },
    ]

    # verify xml export
    export_url = f"/studies/{study.uid}/pharma-cm.xml"
    response = api_client.get(export_url)
    assert_response_status_code(response, 200)
    TestUtils.assert_valid_xml(response.content.decode("utf-8"))


def test_verify_study_duration_fields(
    api_client,
):
    study = TestUtils.create_study()
    ct_terms = TestUtils.get_ct_terms_by_name(name="Study Time").items
    assert (
        len(ct_terms) == 1
    ), "Something is wrong, there should exist just one CTTerm representing StudyTime"
    study_time_unit_subset = ct_terms[0]
    # Adding StudyTime unit subset to `days` unit
    response = api_client.post(
        f"/concepts/unit-definitions/{days_unit_definition.uid}/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/concepts/unit-definitions/{days_unit_definition.uid}",
        json={
            "unit_subsets": [study_time_unit_subset.term_uid],
            "change_description": "Adding to StudyTime unit subset",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/unit-definitions/{days_unit_definition.uid}/approvals",
    )
    assert_response_status_code(response, 201)

    duration_value = 1
    duration_unit = day_unit_definition

    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "study_population": {
                    "planned_maximum_age_of_subjects": {
                        "duration_value": duration_value,
                        "duration_unit_code": {"uid": duration_unit.uid},
                    }
                },
            },
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{study.uid}", params={"include_sections": ["study_population"]}
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["study_population"]["planned_maximum_age_of_subjects"][
            "duration_value"
        ]
        == duration_value
    )
    assert (
        res["current_metadata"]["study_population"]["planned_maximum_age_of_subjects"][
            "duration_unit_code"
        ]["uid"]
        == duration_unit.uid
    )

    duration_value = 2
    duration_unit = days_unit_definition

    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "study_population": {
                    "planned_maximum_age_of_subjects": {
                        "duration_value": duration_value,
                        "duration_unit_code": {"uid": duration_unit.uid},
                    }
                },
            },
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{study.uid}", params={"include_sections": ["study_population"]}
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["current_metadata"]["study_population"]["planned_maximum_age_of_subjects"][
            "duration_value"
        ]
        == duration_value
    )
    assert (
        res["current_metadata"]["study_population"]["planned_maximum_age_of_subjects"][
            "duration_unit_code"
        ]["uid"]
        == duration_unit.uid
    )


def test_get_study_structure_overview(api_client):
    response = api_client.get("/studies/structure-overview")
    assert_response_status_code(response, 200)
    res = response.json()
    assert all(
        i in res["items"][0]
        for i in [
            "study_ids",
            "arms",
            "pre_treatment_epochs",
            "treatment_epochs",
            "no_treatment_epochs",
            "post_treatment_epochs",
            "treatment_elements",
            "no_treatment_elements",
            "cohorts_in_study",
        ]
    )
    assert len(res["items"]) == 2

    response = api_client.get("/studies/structure-overview?page_size=1&page_number=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1


def test_study_structure_overview_grouping(api_client):
    study_with_two_arms = TestUtils.create_study()
    TestUtils.create_study_arm(
        study_uid=study_with_two_arms.uid,
        name="Grouping Arm 1",
        short_name="Grouping Arm 1",
    )
    TestUtils.create_study_arm(
        study_uid=study_with_two_arms.uid,
        name="Grouping Arm 2",
        short_name="Grouping Arm 2",
    )

    response = api_client.get("/studies/structure-overview")
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res["items"]) >= 1

    # Assert grouping semantics: each group has a unique metric signature.
    grouping_keys = [
        "arms",
        "pre_treatment_epochs",
        "treatment_epochs",
        "no_treatment_epochs",
        "post_treatment_epochs",
        "treatment_elements",
        "no_treatment_elements",
        "cohorts_in_study",
    ]
    signatures = [tuple(item[key] for key in grouping_keys) for item in res["items"]]
    assert len(signatures) == len(set(signatures))
    assert any(item["arms"] == 2 for item in res["items"])

    # Ensure groups contain study ids and metric values are in expected domains.
    all_ids = []
    for item in res["items"]:
        assert item["study_ids"]
        assert item["cohorts_in_study"] in ["Y", "N"]
        for key in grouping_keys[:-1]:
            assert item[key] >= 0
        all_ids.extend(item["study_ids"])

    assert all_ids


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("arms"),
        pytest.param("pre_treatment_epochs"),
        pytest.param("treatment_epochs"),
        pytest.param("post_treatment_epochs"),
        pytest.param("no_treatment_epochs"),
        pytest.param("no_treatment_elements"),
        pytest.param("treatment_elements"),
        pytest.param("cohorts_in_study"),
        pytest.param("study_ids"),
    ],
)
def test_get_study_structure_overview_headers(api_client, field_name):
    response = api_client.get(
        f"studies/structure-overview/headers?field_name={field_name}&page_size=100"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param(
            '{"cohorts_in_study": {"v": ["N"], "op": "eq"}}', "cohorts_in_study", "N"
        ),
        pytest.param('{"arms": {"v": [2], "op": "eq"}}', "arms", 2),
        pytest.param('{"*": {"v": ["xyz"], "op": "eq"}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    response = api_client.get(f"studies/structure-overview/?filters={filter_by}")
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result_prefix:
        assert len(res["items"]) > 0
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result_prefix
    else:
        assert len(res["items"]) == 0


def test_study_structure_statistics(
    api_client, tst_study, study_epochs, study_arms, study_elements
):
    response = api_client.get("studies/123000/structure-statistics")
    assert_response_status_code(response, 404)
    response = api_client.get(f"studies/{tst_study.uid}/structure-statistics")
    content = response.json()
    assert content["epoch_count"] == len(study_epochs)
    assert content["arm_count"] == len(study_arms)
    assert content["element_count"] == len(study_elements)
    assert content["visit_count"] == 0
    assert content["cohort_count"] == 0
    assert content["branch_count"] == 0
    assert content["epoch_footnote_count"] == 0
    assert content["visit_footnote_count"] == 0
    assert content["study_activity_count"] == 0
    assert content["study_activity_schedule_count"] == 0


def test_study_structure_statistics_counts_soa_footnotes(
    api_client, tst_study, study_epochs
):
    visit_uid = f"StudyVisit_stats_{random.randint(100000, 999999)}"
    epoch_footnote_uid = (
        f"StudySoAFootnote_epoch_stats_{random.randint(100000, 999999)}"
    )
    visit_footnote_uid = (
        f"StudySoAFootnote_visit_stats_{random.randint(100000, 999999)}"
    )

    db.cypher_query(
        """
        MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
        MATCH (sv)-[:HAS_STUDY_EPOCH]->(epoch:StudyEpoch {uid: $study_epoch_uid})
        CREATE (sv)-[:HAS_STUDY_VISIT]->(:StudyVisit {uid: $study_visit_uid})
        CREATE (sv)-[:HAS_STUDY_FOOTNOTE]->(:StudySoAFootnote {uid: $epoch_footnote_uid})-[:REFERENCES_STUDY_EPOCH]->(epoch)
        WITH sv
        MATCH (sv)-[:HAS_STUDY_VISIT]->(visit:StudyVisit {uid: $study_visit_uid})
        CREATE (sv)-[:HAS_STUDY_FOOTNOTE]->(:StudySoAFootnote {uid: $visit_footnote_uid})-[:REFERENCES_STUDY_VISIT]->(visit)
        """,
        {
            "study_uid": tst_study.uid,
            "study_epoch_uid": study_epochs[0].uid,
            "study_visit_uid": visit_uid,
            "epoch_footnote_uid": epoch_footnote_uid,
            "visit_footnote_uid": visit_footnote_uid,
        },
    )

    response = api_client.get(f"studies/{tst_study.uid}/structure-statistics")
    assert_response_status_code(response, 200)
    content = response.json()
    assert content["epoch_footnote_count"] == 1
    assert content["visit_footnote_count"] == 1


def test_study_selection_containment(api_client, tst_study):
    """Source/target existence and self-comparison (full equality per label)."""
    response = api_client.get(
        f"studies/123000/study-selection-containment/{tst_study.uid}"
    )
    assert_response_status_code(response, 404)
    response = api_client.get(
        f"studies/{tst_study.uid}/study-selection-containment/123000"
    )
    assert_response_status_code(response, 404)
    response = api_client.get(
        f"studies/{tst_study.uid}/study-selection-containment/{tst_study.uid}"
    )
    assert_response_status_code(response, 200)
    data = response.json()
    assert data["target_contained_in_source"]
    for row in data["per_label"]:
        assert row["label_contained"]
        assert row["target_selection_count"] == row["source_selection_count"]
        assert (
            row["target_distinct_ct_term_root_count"]
            == row["source_distinct_ct_term_root_count"]
        )


# pylint: disable=invalid-name
def test_get_studies_list(api_client):
    STUDY_MINIMAL_FIELDS = [
        "uid",
        "id",
        "acronym",
        "subpart_acronym",
    ]
    STUDY_MINIMAL_FIELDS_NOT_NULL = [
        "uid",
    ]
    STUDY_SIMPLE_FIELDS = [
        "uid",
        "id",
        "main_id",
        "acronym",
        "number",
        "title",
        "description",
        "subpart_id",
        "subpart_acronym",
        "clinical_programme_name",
        "project_number",
        "project_name",
        "version_author",
        "version_status",
        "version_start_date",
        "version_number",
        "latest_locked_version",
        "latest_released_version",
        "data_completeness_tags",
    ]
    STUDY_SIMPLE_FIELDS_NOT_NULL = [
        "uid",
        "clinical_programme_name",
        "project_number",
        "project_name",
        "version_author",
        "version_status",
        "version_start_date",
    ]

    response = api_client.get("/studies/list")
    assert_response_status_code(response, 200)
    for item in response.json():
        TestUtils.assert_response_shape_ok(
            item, STUDY_MINIMAL_FIELDS, STUDY_MINIMAL_FIELDS_NOT_NULL
        )

    response = api_client.get("/studies/list?minimal_response=true")
    assert_response_status_code(response, 200)
    for item in response.json():
        TestUtils.assert_response_shape_ok(
            item, STUDY_MINIMAL_FIELDS, STUDY_MINIMAL_FIELDS_NOT_NULL
        )

    response = api_client.get("/studies/list?minimal_response=false")
    assert_response_status_code(response, 200)
    for item in response.json():
        TestUtils.assert_response_shape_ok(
            item, STUDY_SIMPLE_FIELDS, STUDY_SIMPLE_FIELDS_NOT_NULL
        )


def test_get_study_complexity_score(api_client):
    response = api_client.get(f"/studies/{study.uid}/complexity-score")
    assert_response_status_code(response, 200)
    res_latest = response.json()
    assert isinstance(res_latest, float)
    assert res_latest >= 0

    response = api_client.get(
        f"/studies/{study.uid}/complexity-score",
        params={"study_value_version": "1"},
    )
    assert_response_status_code(response, 200)
    res_version_1 = response.json()
    assert isinstance(res_version_1, float)
    assert res_version_1 >= 0


@pytest.mark.parametrize(
    "study_value_version",
    [
        pytest.param(None),
        pytest.param("1"),
    ],
)
def test_get_study_complexity_score_details(api_client, study_value_version):
    params = {"study_value_version": study_value_version} if study_value_version else {}

    # Verify that the `details` endpoint return the same version of the complexity score as the total complexity score endpoint,
    # and that the total complexity score is the sum of the individual components returned in the details endpoint.
    res_total = api_client.get(f"/studies/{study.uid}/complexity-score", params=params)
    res_details = api_client.get(
        f"/studies/{study.uid}/complexity-score-details", params=params
    )
    assert_response_status_code(res_total, 200)
    assert_response_status_code(res_details, 200)

    cs_details = res_details.json()
    assert isinstance(cs_details, dict)
    for component in ["visits", "assessments"]:
        assert component in cs_details
        assert isinstance(cs_details[component], list)
        for item in cs_details[component]:
            assert isinstance(item["type"], str)
            assert isinstance(item["burden"], (int, float))
            assert isinstance(item["count"], (int, float))
            assert item["burden"] >= 0
            assert item["count"] >= 0

    # Assert that the total complexity score is the sum of count * burden for each visit and each assessment
    total_calculated = sum(
        v["count"] * v["burden"] for v in cs_details["visits"]
    ) + sum(a["count"] * a["burden"] for a in cs_details["assessments"])
    assert total_calculated == pytest.approx(res_total.json())


def test_get_integrity_check_for_study(api_client):
    """Test integrity check endpoint for a specific study"""
    study_int = TestUtils.create_study()
    response = api_client.get(f"/studies/{study_int.uid}/integrity-check")
    assert_response_status_code(response, 200)
    res = response.json()

    assert "study_uid" in res
    assert res["study_uid"] == study_int.uid
    assert "all_passed" in res
    assert "checks" in res
    assert isinstance(res["checks"], list)

    # Verify each check has required fields
    for check in res["checks"]:
        assert "check_id" in check
        assert "description" in check
        assert "passed" in check
        assert "noncompliant_count" in check
        assert "noncompliant_node_ids" in check
        assert isinstance(check["noncompliant_node_ids"], list)


def test_get_integrity_check_invalid_study_uid(api_client):
    """Test integrity check endpoint handles invalid study UIDs"""
    invalid_uid = "invalid-uid-12345"
    response = api_client.get(f"/studies/{invalid_uid}/integrity-check")
    assert_response_status_code(
        response, 404
    )  # Should return 404 for non-existent study


def test_concurrent_study_locking_does_not_create_duplicate_sponsor_ct_packages(
    api_client,
):
    """Test that locking multiple studies concurrently does not create duplicate Sponsor CT Packages"""
    from datetime import date

    # Create multiple studies for concurrent locking
    study1 = TestUtils.create_study()
    study2 = TestUtils.create_study()
    study3 = TestUtils.create_study()

    # Update study titles to be able to lock them
    for study_obj in [study1, study2, study3]:
        response = api_client.patch(
            f"/studies/{study_obj.uid}",
            json={
                "current_metadata": {"study_description": {"study_title": "test title"}}
            },
        )
        assert_response_status_code(response, 200)

    # Get initial count of sponsor packages for today
    response = api_client.get(
        f"/ct/packages?sponsor_only=true&catalogue_name={settings.sdtm_ct_catalogue_name}"
    )
    assert_response_status_code(response, 200)
    initial_packages = response.json()
    initial_count_today = len(
        [
            pkg
            for pkg in initial_packages
            if pkg.get("effective_date") == date.today().isoformat()
        ]
    )

    # Lock studies concurrently using threads
    lock_results = []
    errors = []

    def lock_study(study_uid):
        try:
            response = api_client.post(
                f"/studies/{study_uid}/locks",
                json={
                    "change_description": f"Concurrent lock test for {study_uid}",
                    "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                        0
                    ].term_uid,
                },
            )
            lock_results.append((study_uid, response.status_code, response.json()))
        except (ValueError, KeyError, TypeError) as e:
            # Catch specific exceptions that might occur during API call processing
            errors.append((study_uid, str(e)))

    threads = [
        threading.Thread(target=lock_study, args=(study1.uid,)),
        threading.Thread(target=lock_study, args=(study2.uid,)),
        threading.Thread(target=lock_study, args=(study3.uid,)),
    ]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify we got results from all threads
    assert (
        len(lock_results) == 3
    ), f"Expected 3 lock attempts, got {len(lock_results)}. Errors: {errors}"

    # Count successful locks (some may fail due to other validation, but that's OK for this test)
    successful_locks = [r for r in lock_results if r[1] == 201]
    assert len(successful_locks) > 0, (
        f"No successful locks. Results: {lock_results}. "
        f"This test focuses on preventing duplicate packages, not all locks succeeding."
    )

    # Verify only one additional sponsor package was created (or none if it already existed)
    response = api_client.get(
        f"/ct/packages?sponsor_only=true&catalogue_name={settings.sdtm_ct_catalogue_name}"
    )
    assert_response_status_code(response, 200)
    final_packages = response.json()
    final_count_today = len(
        [
            pkg
            for pkg in final_packages
            if pkg.get("effective_date") == date.today().isoformat()
        ]
    )

    # Should have at most one more package than initially (if it didn't exist before)
    # or the same count (if it already existed and was reused)
    assert final_count_today <= initial_count_today + 1
    assert final_count_today >= initial_count_today

    # Verify no duplicate packages exist (same name and date)
    package_names_today = [
        pkg["name"]
        for pkg in final_packages
        if pkg.get("effective_date") == date.today().isoformat()
    ]
    assert len(package_names_today) == len(
        set(package_names_today)
    ), f"Duplicate sponsor packages found: {package_names_today}"


def test_cannot_create_study_with_already_existing_study_acronym(api_client):
    response = api_client.post(
        "/studies",
        json={
            "project_number": "123",
            "study_number": None,
            "study_acronym": "study_root",
            "description": None,
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Study with Study Acronym 'study_root' already exists."


def test_cannot_update_study_to_an_already_existing_study_acronym(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "identification_metadata": {"study_acronym": "study_root"}
            }
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Study with Study Acronym 'study_root' already exists."


def test_study_template_create_patch_retire_reactivate(api_client):
    def _term_uid(value):
        if isinstance(value, dict):
            return value["term_uid"]
        if hasattr(value, "term_uid"):
            return value.term_uid
        return value

    lock_reason_uid = _term_uid(test_data_dict["reason_for_lock_terms"][0])
    release_reason_uid = _term_uid(test_data_dict["reason_for_lock_terms"][0])
    unlock_reason_uid = _term_uid(test_data_dict["reason_for_unlock_terms"][0])

    template_study = TestUtils.create_study()
    template_study_title = "Template study title"
    TestUtils.set_study_title(template_study.uid, study_title=template_study_title)
    lock_response = api_client.post(
        f"/studies/{template_study.uid}/locks",
        json={
            "change_description": "lock template study",
            "reason_for_change_uid": lock_reason_uid,
        },
    )
    assert_response_status_code(lock_response, 201)
    template_version = lock_response.json()["current_metadata"]["version_metadata"][
        "version_number"
    ]

    response = api_client.post(
        "/studies/template",
        json={
            "study_uid": template_study.uid,
            "study_value_version": template_version,
        },
    )
    assert_response_status_code(response, 201)
    created = response.json()
    assert created["study_uid"] == template_study.uid
    assert created["study_value_version"] == template_version
    assert created["status"] == "Final"

    released_study = TestUtils.create_study()
    study_b_title = "Study B title"
    TestUtils.set_study_title(released_study.uid, study_title=study_b_title)
    lock_response = api_client.post(
        f"/studies/{released_study.uid}/locks",
        json={
            "change_description": "lock released study",
            "reason_for_change_uid": lock_reason_uid,
        },
    )
    assert_response_status_code(lock_response, 201)
    response = api_client.post(
        f"/studies/{released_study.uid}/unlocks",
        json={
            "change_description": "Unlock Study B for initial release",
            "reason_for_change_uid": unlock_reason_uid,
        },
    )
    assert_response_status_code(response, 201)
    release_response = api_client.post(
        f"/studies/{released_study.uid}/release",
        json={
            "change_description": "release study",
            "reason_for_change_uid": release_reason_uid,
        },
    )
    assert_response_status_code(release_response, 201)
    # `release` keeps the Study in DRAFT state, so `current_metadata.version_number`
    # in the response can be `None`. Instead, resolve the latest RELEASED snapshot version.
    study_history = (
        StudyService().get_study_snapshot_history(study_uid=released_study.uid).items
    )
    release_history = sorted(
        (item for item in study_history if StudyStatus.RELEASED in item.study_status),
        key=lambda item: item.modified_date,
        reverse=True,
    )
    assert release_history
    released_version = release_history[0].metadata_version
    assert released_version is not None

    response = api_client.patch(
        "/studies/template",
        json={
            "study_uid": released_study.uid,
            "study_value_version": released_version,
            "change_description": "Switch template study",
        },
    )
    assert_response_status_code(response, 200)
    patched = response.json()
    assert patched["study_uid"] == released_study.uid
    assert patched["study_value_version"] == released_version
    assert patched["status"] == "Final"

    response = api_client.get("/studies/template")
    assert_response_status_code(response, 200)
    active_template_v1 = response.json()
    assert active_template_v1["study_uid"] == released_study.uid
    assert active_template_v1["study_value_version"] == released_version

    # Add a second FINAL version for the same StudyB (unlock if needed -> patch short title -> release)
    current_status_response = api_client.get(f"/studies/{released_study.uid}")
    assert_response_status_code(current_status_response, 200)
    current_status = current_status_response.json()["current_metadata"][
        "version_metadata"
    ]["study_status"]
    if current_status == "LOCKED":
        response = api_client.post(
            f"/studies/{released_study.uid}/unlocks",
            json={
                "change_description": "Unlock Study B for v2",
                "reason_for_change_uid": unlock_reason_uid,
            },
        )
        assert_response_status_code(response, 201)

    study_short_title_v2 = TestUtils.random_str(8, prefix="study-short-v2-")
    response = api_client.patch(
        f"/studies/{released_study.uid}",
        json={
            "current_metadata": {
                "study_description": {
                    "study_title": study_b_title,
                    "study_short_title": study_short_title_v2,
                }
            }
        },
    )
    assert_response_status_code(response, 200)

    # Release requires DRAFT; by now the study is expected to be editable.
    release_response_v2 = api_client.post(
        f"/studies/{released_study.uid}/release",
        json={
            "change_description": "Release Study B v2",
            "reason_for_change_uid": release_reason_uid,
        },
    )
    assert_response_status_code(release_response_v2, 201)

    # `release` keeps the Study in DRAFT state, so `current_metadata.version_number`
    # in the response can be `None`. Instead, resolve the latest RELEASED snapshot version.
    study_history = (
        StudyService().get_study_snapshot_history(study_uid=released_study.uid).items
    )
    release_history = sorted(
        (item for item in study_history if StudyStatus.RELEASED in item.study_status),
        key=lambda item: item.modified_date,
        reverse=True,
    )
    assert release_history
    released_version_v2 = release_history[0].metadata_version
    assert released_version_v2 is not None

    # PATCH the template to point to StudyB v2, then GET immediately to verify persistence
    response = api_client.patch(
        "/studies/template",
        json={
            "study_uid": released_study.uid,
            "study_value_version": released_version_v2,
            "change_description": "Switch template study to v2",
        },
    )
    assert_response_status_code(response, 200)
    patched_v2 = response.json()
    assert patched_v2["study_uid"] == released_study.uid
    assert patched_v2["study_value_version"] == released_version_v2
    assert patched_v2["status"] == "Final"

    response = api_client.get("/studies/template")
    assert_response_status_code(response, 200)
    active_template_v2 = response.json()
    assert active_template_v2["study_uid"] == released_study.uid
    assert active_template_v2["study_value_version"] == released_version_v2

    response = api_client.delete("/studies/template/activations")
    assert_response_status_code(response, 200)
    retired = response.json()
    assert retired["status"] == "Retired"

    response = api_client.get("/studies/template")
    assert_response_status_code(response, 200)
    retired_template = response.json()
    assert retired_template is not None
    assert retired_template["status"] == "Retired"
    assert retired_template["uid"] == retired["uid"]
    assert retired_template["study_uid"] == released_study.uid
    assert retired_template["study_value_version"] == released_version_v2

    response = api_client.post("/studies/template/activations")
    assert_response_status_code(response, 200)
    reactivated = response.json()
    assert reactivated["status"] == "Final"
    assert reactivated["study_uid"] == released_study.uid
    assert reactivated["study_value_version"] == released_version_v2

    response = api_client.get("/studies/template")
    assert_response_status_code(response, 200)
    active_template = response.json()
    assert active_template["study_uid"] == released_study.uid
    assert active_template["study_value_version"] == released_version_v2


def test_study_template_rejects_draft_study_version(api_client):
    def _term_uid(value):
        if isinstance(value, dict):
            return value["term_uid"]
        if hasattr(value, "term_uid"):
            return value.term_uid
        return value

    draft_study = TestUtils.create_study()
    TestUtils.set_study_title(draft_study.uid)
    lock_reason_uid = _term_uid(test_data_dict["reason_for_lock_terms"][0])
    unlock_reason_uid = _term_uid(test_data_dict["reason_for_unlock_terms"][0])
    lock_response = api_client.post(
        f"/studies/{draft_study.uid}/locks",
        json={
            "change_description": "lock to create draft later",
            "reason_for_change_uid": lock_reason_uid,
        },
    )
    assert_response_status_code(lock_response, 201)
    unlock_response = api_client.post(
        f"/studies/{draft_study.uid}/unlocks",
        json={"reason_for_change_uid": unlock_reason_uid},
    )
    assert_response_status_code(unlock_response, 201)

    response = api_client.patch(
        "/studies/template",
        json={
            "study_uid": draft_study.uid,
            "study_value_version": "1.1",
            "change_description": "Try draft version",
        },
    )
    assert_response_status_code(response, 404)
    assert "version" in response.json()["message"]


def test_study_template_rejects_empty_target_fields(api_client):
    response = api_client.post(
        "/studies/template",
        json={"study_uid": "", "study_value_version": ""},
    )

    assert_response_status_code(response, 400)
    assert response.json()["details"] == [
        {
            "error_code": "string_too_short",
            "field": ["body", "study_uid"],
            "msg": "String should have at least 1 character",
            "ctx": {"min_length": 1},
        },
        {
            "error_code": "string_too_short",
            "field": ["body", "study_value_version"],
            "msg": "String should have at least 1 character",
            "ctx": {"min_length": 1},
        },
    ]


def _post_or_patch_study_template(
    api_client,
    study_uid: str,
    study_value_version: str,
    *,
    change_description: str,
):
    response = api_client.post(
        "/studies/template",
        json={"study_uid": study_uid, "study_value_version": study_value_version},
    )
    if response.status_code == 400:
        body = response.json()
        if body.get("type") == "BusinessLogicException" and "already exists" in (
            body.get("message") or ""
        ):
            response = api_client.patch(
                "/studies/template",
                json={
                    "study_uid": study_uid,
                    "study_value_version": study_value_version,
                    "change_description": change_description,
                },
            )
    return response


def test_study_template_patch_clears_target_with_empty_study_uid(api_client):
    def _term_uid(value):
        if isinstance(value, dict):
            return value["term_uid"]
        if hasattr(value, "term_uid"):
            return value.term_uid
        return value

    lock_reason_uid = _term_uid(test_data_dict["reason_for_lock_terms"][0])
    template_study = TestUtils.create_study()
    TestUtils.set_study_title(template_study.uid)
    lock_response = api_client.post(
        f"/studies/{template_study.uid}/locks",
        json={
            "change_description": "lock template study",
            "reason_for_change_uid": lock_reason_uid,
        },
    )
    assert_response_status_code(lock_response, 201)
    template_version = lock_response.json()["current_metadata"]["version_metadata"][
        "version_number"
    ]

    response = _post_or_patch_study_template(
        api_client,
        template_study.uid,
        template_version,
        change_description="Seed template for clear-target test",
    )
    assert_response_status_code(response, [200, 201])

    response = api_client.patch(
        "/studies/template",
        json={
            "study_uid": "",
            "study_value_version": "",
            "change_description": "Clear template target",
        },
    )
    assert_response_status_code(response, 200)
    cleared = response.json()
    assert cleared["study_uid"] == ""
    assert cleared["study_value_version"] == ""

    response = api_client.get("/studies/template")
    assert_response_status_code(response, 200)
    persisted = response.json()
    assert persisted["study_uid"] == ""
    assert persisted["study_value_version"] == ""

    response = api_client.patch(
        "/studies/template",
        json={
            "study_uid": "",
            "study_value_version": "ignored-version",
            "change_description": "Clear template target (version ignored)",
        },
    )
    assert_response_status_code(response, 200)
    assert response.json()["study_value_version"] == ""


def test_study_template_patch_requires_version_when_study_uid_set(api_client):
    study = TestUtils.create_study()
    response = api_client.patch(
        "/studies/template",
        json={
            "study_uid": study.uid,
            "study_value_version": "",
            "change_description": "missing version",
        },
    )
    assert_response_status_code(response, 400)


def test_create_study(api_client):
    project_number = TestUtils.random_str(2, "tst")
    project = TestUtils.create_project(
        name="Another test",
        project_number=project_number,
        description="Another test project",
        clinical_programme_uid=test_data_dict["clinical_programme"].uid,
    )

    study_number = "0042"
    response = api_client.post(
        "/studies",
        json={
            "project_number": project.project_number,
            "study_number": study_number,
        },
    )
    res = parse_json_response(response, assert_status=201)

    assert (
        res["current_metadata"]["identification_metadata"]["project_number"]
        == project_number.upper()
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_id"]
        == f"{project_number}-{study_number}".upper()
    )
