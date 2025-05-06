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
from string import ascii_lowercase
from typing import Sequence
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

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
from clinical_mdr_api.models.study_selections.study_standard_version import (
    StudyStandardVersion,
    StudyStandardVersionVersion,
)
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
from clinical_mdr_api.tests.integration.utils.utils import PROJECT_NUMBER, TestUtils
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_USERNAME
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import STUDY_ENDPOINT_TP_NAME

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study

day_unit_definition: UnitDefinitionModel
days_unit_definition: UnitDefinitionModel
week_unit_definition: UnitDefinitionModel
ct_term_study_standard_test: ct_term.CTTerm


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
    inject_base_data()
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
    ct_term_codelist = create_codelist(
        name="Null Flavor",
        uid="CTCodelist",
        catalogue=catalogue_name,
        library=library_name,
    )

    global ct_term_study_standard_test
    ct_term_name = "Not Applicable"
    ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        name_submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime.datetime(2020, 3, 25, tzinfo=datetime.timezone.utc),
        approve=True,
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
    assert_response_status_code(response, 422)


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
    assert_response_status_code(response, 422)

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


def test_study_delete_successful(api_client):
    study_to_delete = TestUtils.create_study()
    response = api_client.delete(f"/studies/{study_to_delete.uid}")
    assert_response_status_code(response, 204)

    response = api_client.get("/studies", params={"deleted": True})
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["uid"] == study_to_delete.uid

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

    # Clean up
    for study in studies:
        response = api_client.delete(f"/studies/{study.uid}")
        assert_response_status_code(response, 204)


def test_get_snapshot_history(api_client):
    study_with_history = TestUtils.create_study()
    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_with_history.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # snapshot history before lock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    res = response.json()
    assert_response_status_code(response, 200)
    res = res["items"]
    assert len(res) == 1
    assert res[0]["possible_actions"] == ["delete", "lock", "release"]
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[0]["current_metadata"]["version_metadata"]["version_number"] is None

    # Lock
    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    # get all standard versions
    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/",
    )
    res: Sequence[StudyStandardVersion] = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["automatically_created"] is True

    # snapshot history after lock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    res = response.json()
    assert_response_status_code(response, 200)
    res = res["items"]
    assert len(res) == 2
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"
    assert res[0]["current_metadata"]["version_metadata"]["version_number"] == "1"
    assert (
        res[0]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 1"
    )
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == "1"
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 1"
    )

    # Unlock
    response = api_client.delete(f"/studies/{study_with_history.uid}/locks")
    assert_response_status_code(response, 200)

    # get all standard versions
    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/",
    )
    res: StudyStandardVersion = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == 0

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study_with_history.uid}/study-standard-versions/audit-trail/",
    )
    res: Sequence[StudyStandardVersionVersion] = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["automatically_created"] is True

    # snapshot history after unlock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert_response_status_code(response, 200)
    res = response.json()
    res = res["items"]
    assert len(res) == 3
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == "1"
    assert res[2]["current_metadata"]["version_metadata"]["version_number"] == "1"

    # Release
    response = api_client.post(
        f"/studies/{study_with_history.uid}/release",
        json={"change_description": "Explicit release"},
    )
    assert_response_status_code(response, 201)
    # snapshot history after release
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert_response_status_code(response, 200)
    res = response.json()
    res = res["items"]

    assert len(res) == 4
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Explicit release"
    )
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == "1.1"
    assert res[2]["current_metadata"]["version_metadata"]["version_number"] == "1"
    assert (
        res[2]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 1"
    )

    # 2nd Release
    response = api_client.post(
        f"/studies/{study_with_history.uid}/release",
        json={"change_description": "Explicit second release"},
    )
    assert_response_status_code(response, 201)
    # snapshot history after second release
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert_response_status_code(response, 200)
    res = response.json()
    res = res["items"]
    assert len(res) == 5
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Explicit second release"
    )
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == "1.2"
    assert res[2]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert res[2]["current_metadata"]["version_metadata"]["version_number"] == "1.1"
    assert (
        res[2]["current_metadata"]["version_metadata"]["version_description"]
        == "Explicit release"
    )

    # Lock
    response = api_client.post(
        f"/studies/{study_with_history.uid}/locks",
        json={"change_description": "Lock 2"},
    )
    assert_response_status_code(response, 201)

    # snapshot history after lock
    response = api_client.get(f"/studies/{study_with_history.uid}/snapshot-history")
    assert_response_status_code(response, 200)
    res = response.json()
    res = res["items"]
    assert len(res) == 6
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"
    assert res[0]["current_metadata"]["version_metadata"]["version_number"] == "2"
    assert (
        res[0]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 2"
    )
    assert res[1]["current_metadata"]["version_metadata"]["study_status"] == "RELEASED"
    assert res[1]["current_metadata"]["version_metadata"]["version_number"] == "2"
    assert (
        res[1]["current_metadata"]["version_metadata"]["version_description"]
        == "Lock 2"
    )


def test_get_default_time_unit(api_client):
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

    response = api_client.get(f"/studies/{study.uid}/time-units")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_uid"] == study.uid
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
        f"/studies/{study.uid}/locks", json={"change_description": "Lock 1"}
    )
    assert_response_status_code(response, 201)

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

    # update study title
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": title_11}}},
    )
    assert_response_status_code(response, 200)

    # Release
    response = api_client.post(
        f"/studies/{study.uid}/release",
        json={"change_description": "Explicit release"},
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
        json={"change_description": "Explicit second release"},
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
        f"/studies/{study.uid}/locks", json={"change_description": "Lock 2"}
    )
    assert_response_status_code(response, 201)

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

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
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_1
    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["study_description"],
            "study_value_version": "1.1",
        },
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_11
    response = api_client.get(
        f"/studies/{study.uid}",
        params={
            "include_sections": ["study_description"],
            "study_value_version": "1.2",
        },
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_12
    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"], "study_value_version": "2"},
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_2
    response = api_client.get(
        f"/studies/{study.uid}",
        params={"include_sections": ["study_description"]},
    )
    res_title = response.json()["current_metadata"]["study_description"]["study_title"]
    assert res_title == title_draft


def test_get_protocol_title_for_specific_version(api_client):
    study = TestUtils.create_study()
    TestUtils.create_library(name="UCUM", is_editable=True)
    codelist = TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)

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
        uid="CTCodelist_00009",
        catalogue=catalogue_name,
        library=library_name,
    )
    type_of_treatment = create_ct_term(
        codelist=type_of_trt_codelist.codelist_uid,
        name="Investigational Product",
        uid="type_of_treatment_00001",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
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

    # response before locking
    response = api_client.get(
        f"/studies/{study.uid}/protocol-title",
    )
    assert_response_status_code(response, 200)
    res_old = response.json()

    TestUtils.set_study_standard_version(study_uid=study.uid)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks", json={"change_description": "Lock 1"}
    )
    assert_response_status_code(response, 201)

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

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


def test_create_study_subpart(api_client):
    response = api_client.post(
        "/studies",
        json={
            "study_subpart_acronym": "sub something",
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
        },
    }
    assert post_res["study_subpart_uids"] == []
    assert post_res["current_metadata"].get("identification_metadata") == {
        "study_number": study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "study_acronym": "new acronym",
        "study_subpart_acronym": "sub something",
        "project_number": "123",
        "project_name": "Project ABC",
        "description": "desc",
        "clinical_programme_name": "CP",
        "study_id": f"{study.current_metadata.identification_metadata.study_id}-a",
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
        },
    }
    assert get_res["study_subpart_uids"] == []
    assert get_res["current_metadata"].get("identification_metadata") == {
        "study_number": study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "study_acronym": "new acronym",
        "study_subpart_acronym": "sub something",
        "project_number": "123",
        "project_name": "Project ABC",
        "description": "desc",
        "clinical_programme_name": "CP",
        "study_id": f"{study.current_metadata.identification_metadata.study_id}-a",
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
                    "study_subpart_acronym": "sub something",
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
        },
    }
    assert post_res["study_subpart_uids"] == []
    assert post_res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "study_subpart_acronym": "sub something",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": new_study.current_metadata.identification_metadata.description,
        "clinical_programme_name": "CP",
        "study_id": f"{parent_study.current_metadata.identification_metadata.study_id}-a",
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
        },
    }
    assert get_res["study_subpart_uids"] == []
    assert get_res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_study.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": parent_study.current_metadata.identification_metadata.study_acronym,
        "study_subpart_acronym": "sub something",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": new_study.current_metadata.identification_metadata.description,
        "clinical_programme_name": "CP",
        "study_id": f"{parent_study.current_metadata.identification_metadata.study_id}-a",
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
        }

    TestUtils.set_study_standard_version(study_uid=parent_study.uid)

    response = api_client.post(
        f"/studies/{parent_study.uid}/locks",
        json={"change_description": "Locked"},
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "LOCKED"
    _check_study_subparts_status("LOCKED")

    response = api_client.delete(f"/studies/{parent_study.uid}/locks")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    _check_study_subparts_status("DRAFT")

    response = api_client.post(
        f"/studies/{parent_study.uid}/release",
        json={"change_description": "Released"},
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    _check_study_subparts_status("DRAFT")


def test_reordering_study_subparts(api_client):
    parent_study = TestUtils.create_study()
    new_studies = [
        TestUtils.create_study(study_parent_part_uid=parent_study.uid)
        for _ in range(10)
    ]

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
                    "study_subpart_acronym": "sub something",
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
        },
    }
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"].get("identification_metadata") == {
        "study_number": parent_part.current_metadata.identification_metadata.study_number,
        "subpart_id": "a",
        "project_number": "123",
        "study_acronym": parent_part.current_metadata.identification_metadata.study_acronym,
        "study_subpart_acronym": "sub something",
        "project_name": new_study.current_metadata.identification_metadata.project_name,
        "description": None,
        "clinical_programme_name": "CP",
        "study_id": f"{parent_part.current_metadata.identification_metadata.study_id}-a",
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
        "clinical_programme_name": "CP",
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
        },
    }
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert (
        res["current_metadata"]["version_metadata"]["version_author"] == AUTHOR_USERNAME
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None


# pylint: disable=too-many-statements
def test_get_audit_trail_of_all_study_subparts_of_study(api_client):
    response = api_client.get("/studies/Study_000025/audit-trail")
    assert_response_status_code(response, 200)
    res = response.json()
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
        assert i in res[0]

    assert len(res) == 36

    assert res[0]["subpart_id"] == "i"
    assert res[0]["subpart_uid"] == "Study_000034"
    assert res[1]["subpart_id"] == "h"
    assert res[1]["subpart_uid"] == "Study_000033"
    assert res[2]["subpart_id"] == "g"
    assert res[2]["subpart_uid"] == "Study_000032"
    assert res[3]["subpart_id"] == "f"
    assert res[3]["subpart_uid"] == "Study_000030"
    assert res[4]["subpart_id"] == "e"
    assert res[4]["subpart_uid"] == "Study_000029"
    assert res[5]["subpart_id"] == "d"
    assert res[5]["subpart_uid"] == "Study_000031"
    assert res[6]["subpart_id"] == "c"
    assert res[6]["subpart_uid"] == "Study_000027"
    assert res[7]["subpart_id"] == "b"
    assert res[7]["subpart_uid"] == "Study_000026"
    assert res[8]["subpart_id"] == "a"
    assert res[8]["subpart_uid"] == "Study_000028"
    assert res[9]["subpart_id"] == "j"
    assert res[9]["subpart_uid"] == "Study_000035"
    assert res[10]["subpart_id"] == "a"
    assert res[10]["subpart_uid"] == "Study_000035"
    assert res[11]["subpart_id"] == "j"
    assert res[11]["subpart_uid"] == "Study_000034"
    assert res[12]["subpart_id"] == "i"
    assert res[12]["subpart_uid"] == "Study_000033"
    assert res[13]["subpart_id"] == "h"
    assert res[13]["subpart_uid"] == "Study_000032"
    assert res[14]["subpart_id"] == "g"
    assert res[14]["subpart_uid"] == "Study_000030"
    assert res[15]["subpart_id"] == "f"
    assert res[15]["subpart_uid"] == "Study_000029"
    assert res[16]["subpart_id"] == "e"
    assert res[16]["subpart_uid"] == "Study_000031"
    assert res[17]["subpart_id"] == "d"
    assert res[17]["subpart_uid"] == "Study_000027"
    assert res[18]["subpart_id"] == "c"
    assert res[18]["subpart_uid"] == "Study_000026"
    assert res[19]["subpart_id"] == "b"
    assert res[19]["subpart_uid"] == "Study_000028"
    assert res[20]["subpart_id"] == "d"
    assert res[20]["subpart_uid"] == "Study_000031"
    assert res[21]["subpart_id"] == "f"
    assert res[21]["subpart_uid"] == "Study_000030"
    assert res[22]["subpart_id"] == "e"
    assert res[22]["subpart_uid"] == "Study_000029"
    assert res[23]["subpart_id"] == "a"
    assert res[23]["subpart_uid"] == "Study_000028"
    assert res[24]["subpart_id"] == "c"
    assert res[24]["subpart_uid"] == "Study_000027"
    assert res[25]["subpart_id"] == "b"
    assert res[25]["subpart_uid"] == "Study_000026"
    assert res[26]["subpart_id"] == "j"
    assert res[26]["subpart_uid"] == "Study_000035"
    assert res[27]["subpart_id"] == "i"
    assert res[27]["subpart_uid"] == "Study_000034"
    assert res[28]["subpart_id"] == "h"
    assert res[28]["subpart_uid"] == "Study_000033"
    assert res[29]["subpart_id"] == "g"
    assert res[29]["subpart_uid"] == "Study_000032"
    assert res[30]["subpart_id"] == "f"
    assert res[30]["subpart_uid"] == "Study_000031"
    assert res[31]["subpart_id"] == "e"
    assert res[31]["subpart_uid"] == "Study_000030"
    assert res[32]["subpart_id"] == "d"
    assert res[32]["subpart_uid"] == "Study_000029"
    assert res[33]["subpart_id"] == "c"
    assert res[33]["subpart_uid"] == "Study_000028"
    assert res[34]["subpart_id"] == "b"
    assert res[34]["subpart_uid"] == "Study_000027"
    assert res[35]["subpart_id"] == "a"
    assert res[35]["subpart_uid"] == "Study_000026"

    # update study title to be able to lock it
    response = api_client.patch(
        "/studies/Study_000025",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    TestUtils.set_study_standard_version(study_uid="Study_000025")

    # Lock
    response = api_client.post(
        "/studies/Study_000025/locks", json={"change_description": "version Lock"}
    )
    assert_response_status_code(response, 201)

    # Unlock
    response = api_client.delete("/studies/Study_000025/locks")
    assert_response_status_code(response, 200)

    response = api_client.patch(
        "/studies/Study_000026",
        json={
            "study_parent_part_uid": None,
            "current_metadata": {
                "identification_metadata": {
                    "study_number": "3333",
                }
            },
        },
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        "/studies/Study_000025/locks", json={"change_description": "version Lock"}
    )
    assert_response_status_code(response, 201)

    # Unlock
    response = api_client.delete("/studies/Study_000025/locks")
    assert_response_status_code(response, 200)

    response = api_client.get("/studies/Study_000025/audit-trail?study_value_version=1")
    assert_response_status_code(response, 200)
    res = response.json()
    assert all(i["end_date"] for i in res if i["subpart_uid"] == "Study_000026")


def test_get_audit_trail_of_study_subpart(api_client):
    response = api_client.get("/studies/Study_000030/audit-trail?is_subpart=true")
    assert_response_status_code(response, 200)
    res = response.json()
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
        assert i in res[0]

    assert len(res) == 11

    assert res[0]["subpart_id"] == "e"
    assert res[0]["subpart_uid"] == "Study_000030"
    assert res[1]["subpart_id"] == "e"
    assert res[1]["subpart_uid"] == "Study_000030"
    assert res[2]["subpart_id"] == "e"
    assert res[2]["subpart_uid"] == "Study_000030"
    assert res[3]["subpart_id"] == "e"
    assert res[3]["subpart_uid"] == "Study_000030"
    assert res[4]["subpart_id"] == "f"
    assert res[4]["subpart_uid"] == "Study_000030"
    assert res[5]["subpart_id"] == "f"
    assert res[5]["subpart_uid"] == "Study_000030"
    assert res[6]["subpart_id"] == "f"
    assert res[6]["subpart_uid"] == "Study_000030"
    assert res[7]["subpart_id"] == "f"
    assert res[7]["subpart_uid"] == "Study_000030"
    assert res[8]["subpart_id"] == "g"
    assert res[8]["subpart_uid"] == "Study_000030"
    assert res[9]["subpart_id"] == "f"
    assert res[9]["subpart_uid"] == "Study_000030"
    assert res[10]["subpart_id"] == "e"
    assert res[10]["subpart_uid"] == "Study_000030"


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
    assert_response_status_code(response, 422)
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
    response = api_client.delete(f"/studies/{study.uid}")
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"Study {study.uid}: cannot delete a Study having Study Subparts: ['Study_000053', 'Study_000011']."
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
        "/studies/Study_000011/locks", json={"change_description": "Lock"}
    )
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be locked independently from its Study Parent Part with UID 'Study_000002'."
    )


def test_cannot_unlock_study_subpart(api_client):
    response = api_client.delete("/studies/Study_000011/locks")
    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Study Subparts cannot be unlocked independently from its Study Parent Part with UID 'Study_000002'."
    )


def test_cannot_release_study_subpart(api_client):
    response = api_client.post(
        "/studies/Study_000011/release", json={"change_description": "Lock"}
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
        f"/studies/{_study.uid}/locks", json={"change_description": "Lock"}
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
                    "study_subpart_acronym": "sub something",
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
                    "study_number": "1111",
                }
            },
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Study with Study Number '1111' already exists."


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
    inclusion_criteria_term = "INCLUSION CRITERIA"
    ct_term_inclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name=inclusion_criteria_term,
        sponsor_preferred_name_sentence_case=inclusion_criteria_term.lower(),
    )
    exclusion_criteria_term = "EXCLUSION CRITERIA"
    ct_term_exclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name=exclusion_criteria_term,
        sponsor_preferred_name_sentence_case=exclusion_criteria_term.lower(),
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
    TestUtils.create_template_parameter(STUDY_ENDPOINT_TP_NAME)

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

    arm_type = "Investigational Arm"
    investigational_arm = TestUtils.create_ct_term(
        sponsor_preferred_name=arm_type,
        sponsor_preferred_name_sentence_case=arm_type.lower(),
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
        res["number_of_subjects"]
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
    response = api_client.get("/studies/structure-overview")
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res["items"][0]["study_ids"]) == 62
    assert res["items"][0]["arms"] == 0
    assert res["items"][0]["pre_treatment_epochs"] == 0
    assert res["items"][0]["treatment_epochs"] == 0
    assert res["items"][0]["no_treatment_epochs"] == 0
    assert res["items"][0]["post_treatment_epochs"] == 0
    assert res["items"][0]["treatment_elements"] == 0
    assert res["items"][0]["no_treatment_elements"] == 0
    assert res["items"][0]["cohorts_in_study"] == "N"

    assert len(res["items"][1]["study_ids"]) == 1
    assert res["items"][1]["arms"] == 2
    assert res["items"][1]["pre_treatment_epochs"] == 0
    assert res["items"][1]["treatment_epochs"] == 0
    assert res["items"][1]["no_treatment_epochs"] == 0
    assert res["items"][1]["post_treatment_epochs"] == 0
    assert res["items"][1]["treatment_elements"] == 0
    assert res["items"][1]["no_treatment_elements"] == 0
    assert res["items"][1]["cohorts_in_study"] == "N"


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
