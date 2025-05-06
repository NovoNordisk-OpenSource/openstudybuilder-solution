"""
Tests for /listings/studies/all/adam/ endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.listings.listings_sdtm import StudyElementListing
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
    get_codelist_with_term_cypher,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    add_parent_ct_term,
    create_codelist,
    create_ct_term,
    create_study_element_with_planned_duration,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    generate_study_root,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import CDISC_LIBRARY_NAME, SDTM_CT_CATALOGUE_NAME

study_uid: str

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    global study_uid
    study_uid = "study_root"
    inject_and_clear_db("SDTMTEListingTest.api")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    study = generate_study_root()
    # Create an epoch
    create_study_epoch_codelists_ret_cat_and_lib()
    catalogue_name, library_name = get_catalogue_name_library_name()
    create_study_epoch("EpochSubType_0001")
    create_study_epoch("EpochSubType_0001")

    element_type_term_uid1 = "ElementTypeTermUid_1"
    db.cypher_query(
        get_codelist_with_term_cypher(
            name="No Treatment",
            codelist_name="Element Type",
            codelist_uid="ElementTypeCodelistUid",
            term_uid=element_type_term_uid1,
        )
    )

    element_subtype_term_uid1 = "ElementSubTypeTermUid_1"
    db.cypher_query(
        get_codelist_with_term_cypher(
            name="Screening",
            codelist_name="Element Sub Type",
            codelist_uid="ElementSubTypeCodelistUid",
            term_uid=element_subtype_term_uid1,
        )
    )
    add_parent_ct_term(element_subtype_term_uid1, element_type_term_uid1)

    element_subtype_term_uid2 = "ElementSubTypeTermUid_2"
    db.cypher_query(
        get_codelist_with_term_cypher(
            name="Wash-out",
            codelist_name="Element Sub Type",
            codelist_uid="ElementSubTypeCodelistUid",
            term_uid=element_subtype_term_uid2,
        )
    )
    add_parent_ct_term(element_subtype_term_uid2, element_type_term_uid1)

    codelist = create_codelist(
        name="time",
        uid="C66781",
        catalogue=catalogue_name,
        library=library_name,
    )
    ct_term_uid = "hours001"
    hour_term = create_ct_term(
        codelist=codelist.codelist_uid,
        name="hours",
        uid=ct_term_uid,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )
    subset_codelist = create_codelist(
        name="Unit Subset",
        uid="UnitSubsetCuid",
        catalogue=catalogue_name,
        library=library_name,
    )
    study_time_subset = create_ct_term(
        codelist=subset_codelist.codelist_uid,
        name="Study Time",
        uid="StudyTimeSuid",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )
    unit_def = TestUtils.create_unit_definition(
        name="hours",
        library_name="Sponsor",
        ct_units=[hour_term.uid],
        unit_subsets=[study_time_subset.uid],
    )
    create_study_element_with_planned_duration(
        element_type_term_uid1, study.uid, unit_definition_uid=unit_def.uid
    )
    create_study_element_with_planned_duration(
        element_type_term_uid1, study.uid, unit_definition_uid=unit_def.uid
    )
    TestUtils.create_study_fields_configuration()
    # Creating library and catalogue for study standard version
    TestUtils.create_library(name=CDISC_LIBRARY_NAME, is_editable=True)
    TestUtils.create_ct_catalogue(
        library=CDISC_LIBRARY_NAME, catalogue_name=SDTM_CT_CATALOGUE_NAME
    )
    TestUtils.set_study_standard_version(study_uid=study.uid)

    fix_study_preferred_time_unit(study.uid)


def test_te_listing(api_client):
    response = api_client.get(
        "/listings/studies/study_root/sdtm/te",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None

    expected_output = [
        StudyElementListing(
            DOMAIN="TE",
            ELEMENT="Element_Name_1",
            ETCD="1",
            STUDYID="SOME_ID-0",
            TEDUR="P70H",
            TEENRL="stop_rule",
            TESTRL="start_rule",
        ).model_dump(),
        # 1
        StudyElementListing(
            DOMAIN="TE",
            ELEMENT="Element_Name_1",
            ETCD="2",
            STUDYID="SOME_ID-0",
            TEDUR="P70H",
            TEENRL="stop_rule",
            TESTRL="start_rule",
        ).model_dump(),
    ]
    assert res == expected_output


def test_te_listing_versioning(api_client):
    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study_uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        "/listings/studies/study_root/sdtm/te",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None
    te_before_unlock = res

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study_uid}/locks")
    assert_response_status_code(response, 200)

    # get all visits
    response = api_client.get(
        f"/studies/{study_uid}/study-element/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

    # edit element
    response = api_client.patch(
        f"/studies/{study_uid}/study-elements/{old_res[0]['element_uid']}",
        json={
            "name": "New_Element_Name_1",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "New_Element_Name_1"

    # get all study visits of a specific study version
    response = api_client.get(
        f"/listings/studies/{study_uid}/sdtm/te?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"] == te_before_unlock
    assert res["items"][0]["ELEMENT"] != "New_Element_Name_1"

    response = api_client.get(
        "/listings/studies/study_root/sdtm/te",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[0]["ELEMENT"] == "New_Element_Name_1"
