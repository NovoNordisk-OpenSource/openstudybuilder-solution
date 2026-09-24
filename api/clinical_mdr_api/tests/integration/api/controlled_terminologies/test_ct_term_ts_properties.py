"""
Tests that TS (Trial Summary) properties are returned conditionally:
  - Only for terms belonging to the TS codelists (C66738 / C67152).
  - Non-TS terms must have null TS properties.

Endpoints under test:
  GET /ct/terms              (aggregated, via ct_term_aggregated_repository)
  GET /ct/terms/names        (names only, via ct_term_generic_repository)
  GET /ct/terms/{uid}/names  (single term, via library_item_repository)
  PATCH /ct/terms/{uid}/names/trial-summary-parameters  (save path)
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import json
import logging

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import (
    CTTermNameTSParameterInput,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)

TS_TERM_UID = "C99079"
NON_TS_TERM_UID: str = ""  # set during fixture setup

TS_FIELDS = (
    "osb_field_name",
    "osb_page_reference",
    "semantic_data_type",
    "response_codelist",
    "response_dictionary_uids",
    "valid_null_flavor_terms",
)


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Set up a minimal database with:
    - A TS codelist (C66738) containing one term linked to a MetaStudyField
    - A regular (non-TS) codelist containing a plain term
    """
    db_name = "ct-term-ts-properties.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False)

    catalogue_name = "SDTM CT"
    library_name = "Sponsor"

    # --- TS codelist (C66738 = TSPARMCD) ---
    ts_code_codelist = create_codelist(
        name="Trial Summary Parameter Test Code",
        uid="C66738",
        catalogue=catalogue_name,
        library=library_name,
    )

    # --- Data type codelist (needed for semantic_data_type_uid) ---
    dt_codelist = create_codelist(
        name="Data Type",
        uid="CTCodelist_DataType",
        catalogue=settings.ddf_ct_catalogue_name,
        library=library_name,
        submission_value=settings.data_type_cl_submval,
    )
    create_ct_term(
        name="Text",
        uid="DT_TEXT",
        preferred_term="Text",
        definition="Data type: Text",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {"uid": dt_codelist.codelist_uid, "order": 1, "submission_value": "Text"}
        ],
    )

    # --- Response codelist (for response_codelist_uid) ---
    response_codelist = create_codelist(
        name="Yes No Response",
        uid="CTCodelist_YesNo",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="NY",
    )

    # --- Null flavor codelist and term (for valid_null_flavor_term_uids) ---
    nf_codelist = create_codelist(
        name="Null Flavor",
        uid="CTCodelist_NullFlavor",
        catalogue=catalogue_name,
        library=library_name,
        submission_value=settings.null_flavor_cl_submval,
    )
    create_ct_term(
        name="Not Applicable",
        uid="NF_NA",
        preferred_term="Not Applicable",
        definition="Null flavor: Not Applicable",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {"uid": nf_codelist.codelist_uid, "order": 1, "submission_value": "NA"}
        ],
    )

    # --- TS term in C66738 ---
    create_ct_term(
        name="Study Short Title",
        uid=TS_TERM_UID,
        preferred_term="Study Short Title",
        definition="A short title for the study.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": ts_code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "SHORTTL",
            },
        ],
    )

    # Link TS term to MetaStudyField + data type via patch_trial_summary_parameter
    ts_service = CTTermNameService()
    ts_service.patch_trial_summary_parameter(
        TS_TERM_UID,
        CTTermNameTSParameterInput(
            osb_field_name="study_short_title",
            semantic_data_type_uid="DT_TEXT",
            response_codelist_uid=response_codelist.codelist_uid,
            valid_null_flavor_term_uids=["NF_NA"],
            reference="ClinicalTrials.gov",
            required_level="Required",
            cardinality="One",
            notes="Short title of the study.",
            osb_page_reference="p.42",
        ),
    )
    ts_service.approve(TS_TERM_UID)

    # --- Non-TS term (in default codelist C66737) ---
    global NON_TS_TERM_UID
    non_ts_term = TestUtils.create_ct_term(sponsor_preferred_name="plain_term")
    NON_TS_TERM_UID = non_ts_term.term_uid

    yield


# ---------- GET /ct/terms (aggregated) ----------


def test_get_ct_terms_ts_term_has_ts_properties(api_client):
    """GET /ct/terms returns TS properties for a term in codelist C66738."""
    response = api_client.get(
        "/ct/terms",
        params={
            "codelist_uid": "C66738",
            "page_size": 50,
            "include_ts_parameters": True,
        },
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    ts_items = [i for i in items if i["term_uid"] == TS_TERM_UID]
    assert len(ts_items) >= 1, f"Expected TS term {TS_TERM_UID} in results"
    ts_item = ts_items[0]

    assert ts_item["name"]["osb_field_name"] == "study_short_title"
    assert ts_item["name"]["semantic_data_type"]["uid"] == "DT_TEXT"
    assert ts_item["name"]["response_codelist"]["uid"] == "CTCodelist_YesNo"
    assert ts_item["name"]["valid_null_flavor_terms"][0]["uid"] == "NF_NA"
    assert ts_item["name"]["reference"] == "ClinicalTrials.gov"
    assert ts_item["name"]["required_level"] == "Required"
    assert ts_item["name"]["cardinality"] == "One"
    assert ts_item["name"]["notes"] == "Short title of the study."
    assert ts_item["name"]["osb_page_reference"] == "p.42"


def test_get_ct_terms_non_ts_term_has_null_ts_properties(api_client):
    """GET /ct/terms returns null TS properties for a term NOT in a TS codelist."""
    response = api_client.get(
        "/ct/terms",
        params={
            "codelist_uid": "C66737",
            "page_size": 50,
            "include_ts_parameters": True,
        },
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    non_ts_items = [i for i in items if i["term_uid"] == NON_TS_TERM_UID]
    assert len(non_ts_items) >= 1, f"Expected non-TS term {NON_TS_TERM_UID} in results"
    non_ts_item = non_ts_items[0]

    assert non_ts_item["name"]["osb_field_name"] is None
    assert non_ts_item["name"]["semantic_data_type"] is None
    assert non_ts_item["name"]["response_codelist"] is None


# ---------- GET /ct/terms/names (generic / bulk names) ----------


def test_get_ct_term_names_ts_term_has_ts_properties(api_client):
    """GET /ct/terms/names returns TS properties for a term in codelist C66738."""
    response = api_client.get(
        "/ct/terms/names",
        params={
            "codelist_uid": "C66738",
            "page_size": 50,
            "include_ts_parameters": True,
        },
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    ts_items = [i for i in items if i["term_uid"] == TS_TERM_UID]
    assert len(ts_items) >= 1, f"Expected TS term {TS_TERM_UID} in results"
    ts_item = ts_items[0]

    assert ts_item["osb_field_name"] == "study_short_title"
    assert ts_item["semantic_data_type"]["uid"] == "DT_TEXT"
    assert ts_item["response_codelist"]["uid"] == "CTCodelist_YesNo"
    assert ts_item["valid_null_flavor_terms"][0]["uid"] == "NF_NA"
    assert ts_item["reference"] == "ClinicalTrials.gov"
    assert ts_item["required_level"] == "Required"
    assert ts_item["cardinality"] == "One"
    assert ts_item["notes"] == "Short title of the study."
    assert ts_item["osb_page_reference"] == "p.42"


def test_get_ct_term_names_non_ts_term_has_null_ts_properties(api_client):
    """GET /ct/terms/names returns null TS properties for a non-TS term."""
    response = api_client.get(
        "/ct/terms/names",
        params={
            "codelist_uid": "C66737",
            "page_size": 50,
            "include_ts_parameters": True,
        },
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    non_ts_items = [i for i in items if i["term_uid"] == NON_TS_TERM_UID]
    assert len(non_ts_items) >= 1, f"Expected non-TS term {NON_TS_TERM_UID} in results"
    non_ts_item = non_ts_items[0]

    assert non_ts_item["osb_field_name"] is None
    assert non_ts_item["semantic_data_type"] is None
    assert non_ts_item["response_codelist"] is None


# ---------- GET /ct/terms/{term_uid}/names (single item) ----------


def test_get_ct_term_by_uid_ts_term_has_ts_properties(api_client):
    """GET /ct/terms/{uid}/names returns TS properties for a TS term."""
    response = api_client.get(
        f"/ct/terms/{TS_TERM_UID}/names",
        params={"include_ts_parameters": True},
    )
    assert_response_status_code(response, 200)
    data = response.json()

    assert data["osb_field_name"] == "study_short_title"
    assert data["semantic_data_type"]["uid"] == "DT_TEXT"
    assert data["response_codelist"]["uid"] == "CTCodelist_YesNo"
    assert data["valid_null_flavor_terms"][0]["uid"] == "NF_NA"
    assert data["reference"] == "ClinicalTrials.gov"
    assert data["required_level"] == "Required"
    assert data["cardinality"] == "One"
    assert data["notes"] == "Short title of the study."
    assert data["osb_page_reference"] == "p.42"


def test_get_ct_term_by_uid_non_ts_term_has_null_ts_properties(api_client):
    """GET /ct/terms/{uid}/names returns null TS properties for a non-TS term."""
    response = api_client.get(
        f"/ct/terms/{NON_TS_TERM_UID}/names",
        params={"include_ts_parameters": True},
    )
    assert_response_status_code(response, 200)
    data = response.json()

    assert data["osb_field_name"] is None
    assert data["semantic_data_type"] is None
    assert data["response_codelist"] is None


# ---------- GET /ct/codelists/{codelist_uid}/terms ----------


def test_get_codelist_terms_ts_term_has_ts_properties(api_client):
    """GET /ct/codelists/{uid}/terms returns TS properties for terms in a TS codelist."""
    response = api_client.get(
        "/ct/codelists/C66738/terms",
        params={"page_size": 50, "include_ts_parameters": True},
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    ts_items = [i for i in items if i["term_uid"] == TS_TERM_UID]
    assert (
        len(ts_items) >= 1
    ), f"Expected TS term {TS_TERM_UID} in codelist terms results"
    ts_item = ts_items[0]

    assert ts_item["osb_field_name"] == "study_short_title"
    assert ts_item["semantic_data_type"] is not None
    assert ts_item["semantic_data_type"]["uid"] == "DT_TEXT"
    assert ts_item["response_codelist"]["uid"] == "CTCodelist_YesNo"
    assert ts_item["valid_null_flavor_terms"][0]["uid"] == "NF_NA"
    assert ts_item["response_dictionary_uids"] == []
    assert ts_item["reference"] == "ClinicalTrials.gov"
    assert ts_item["required_level"] == "Required"
    assert ts_item["cardinality"] == "One"
    assert ts_item["notes"] == "Short title of the study."
    assert ts_item["osb_page_reference"] == "p.42"


def test_get_codelist_terms_filter_by_submission_value(api_client):
    """GET /ct/codelists/{uid}/terms must accept filters on submission_value.

    Regression for 400 caused by mapping `submission_value` to
    `value_node.submission_value` on a query that has no `value_node` alias.
    """
    filters = json.dumps({"submission_value": {"v": ["SHORTTL"], "op": "eq"}})

    response = api_client.get(
        "/ct/codelists/C66738/terms",
        params={
            "page_size": 50,
            "total_count": True,
            "filters": filters,
        },
    )

    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["term_uid"] == TS_TERM_UID
    assert items[0]["submission_value"] == "SHORTTL"


def test_get_codelist_terms_wildcard_filter_supports_ts_array_fields(api_client):
    """Wildcard filtering on codelist terms must not fail when TS list fields are present.

    Regression for 500 error caused by applying toLower() directly to list-valued
    TS fields such as `response_dictionary_uids` / `valid_null_flavor_terms`.
    """
    wildcard_filter = json.dumps({"*": {"v": ["title"], "op": "co"}})

    response = api_client.get(
        "/ct/codelists/C66738/terms",
        params={
            "page_size": 50,
            "total_count": True,
            "filters": wildcard_filter,
            "include_ts_parameters": True,
        },
    )

    assert_response_status_code(response, 200)
    payload = response.json()
    items = payload["items"]
    assert isinstance(items, list)
    assert len(items) >= 1


def test_get_codelist_terms_non_ts_term_has_null_ts_properties(api_client):
    """GET /ct/codelists/{uid}/terms returns null TS properties for a non-TS codelist."""
    response = api_client.get(
        "/ct/codelists/C66737/terms",
        params={"page_size": 50, "include_ts_parameters": True},
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    non_ts_items = [i for i in items if i["term_uid"] == NON_TS_TERM_UID]
    assert (
        len(non_ts_items) >= 1
    ), f"Expected non-TS term {NON_TS_TERM_UID} in codelist terms results"
    non_ts_item = non_ts_items[0]

    assert non_ts_item["osb_field_name"] is None
    assert non_ts_item["semantic_data_type"] is None
    assert non_ts_item["response_codelist"] is None
    assert non_ts_item["response_dictionary_uids"] == []
    assert non_ts_item["valid_null_flavor_terms"] == []


# ---------- PATCH /ct/terms/{uid}/names/trial-summary-parameters (save path) ----------


def test_patch_ts_parameter_saves_osb_page_reference(api_client):
    """PATCH endpoint persists osb_page_reference and returns it in the response."""
    new_value = "p.99"

    # --- Update ---
    patch_response = api_client.patch(
        f"/ct/terms/{TS_TERM_UID}/names/trial-summary-parameters",
        json={
            "osb_field_name": "study_short_title",
            "semantic_data_type_uid": "DT_TEXT",
            "response_codelist_uid": "CTCodelist_YesNo",
            "valid_null_flavor_term_uids": ["NF_NA"],
            "reference": "ClinicalTrials.gov",
            "required_level": "Required",
            "cardinality": "One",
            "notes": "Short title of the study.",
            "osb_page_reference": new_value,
        },
    )
    assert_response_status_code(patch_response, 200)
    patch_data = patch_response.json()
    assert (
        patch_data["osb_page_reference"] == new_value
    ), f"PATCH response did not include updated osb_page_reference: {patch_data}"

    # --- Verify persistence via GET ---
    get_response = api_client.get(
        f"/ct/terms/{TS_TERM_UID}/names",
        params={"include_ts_parameters": True},
    )
    assert_response_status_code(get_response, 200)
    assert get_response.json()["osb_page_reference"] == new_value

    # --- Restore original so subsequent tests remain valid ---
    restore_response = api_client.patch(
        f"/ct/terms/{TS_TERM_UID}/names/trial-summary-parameters",
        json={
            "osb_field_name": "study_short_title",
            "semantic_data_type_uid": "DT_TEXT",
            "response_codelist_uid": "CTCodelist_YesNo",
            "valid_null_flavor_term_uids": ["NF_NA"],
            "reference": "ClinicalTrials.gov",
            "required_level": "Required",
            "cardinality": "One",
            "notes": "Short title of the study.",
            "osb_page_reference": "p.42",
        },
    )
    assert_response_status_code(restore_response, 200)
    assert restore_response.json()["osb_page_reference"] == "p.42"


# ---------- POST /ct/terms with ts_parameter (create path) ----------


def test_post_ct_term_with_ts_parameter_persists_all_fields(api_client):
    """POST /ct/terms with `ts_parameter` populated must persist every TS scalar
    property and wire every TS graph relationship on the initial save, so that
    the subsequent GET returns them without any follow-up PATCH."""
    create_response = api_client.post(
        "/ct/terms",
        json={
            "catalogue_names": ["SDTM CT"],
            "codelists": [
                {
                    "codelist_uid": "C66738",
                    "submission_value": "POSTTSCREATE",
                    "order": 99,
                }
            ],
            "library_name": "Sponsor",
            "definition": "Term created with TS parameter properties in one shot.",
            "sponsor_preferred_name": "TS Param Created Term",
            "sponsor_preferred_name_sentence_case": "ts param created term",
            "ts_parameter": {
                "osb_field_name": "study_post_create_field",
                "osb_page_reference": "p.7",
                "semantic_data_type_uid": "DT_TEXT",
                "response_codelist_uid": "CTCodelist_YesNo",
                "valid_null_flavor_term_uids": ["NF_NA"],
                "reference": "ClinicalTrials.gov",
                "required_level": "Required",
                "cardinality": "One",
                "notes": "Created via POST /ct/terms with ts_parameter.",
            },
        },
    )
    assert_response_status_code(create_response, 201)
    new_term_uid = create_response.json()["term_uid"]

    # Approve the name version so that _maintain_parameters has wired the TS rels
    # (POST /ct/terms creates DRAFT records by default; approve to make TS reads return).
    api_client.post(f"/ct/terms/{new_term_uid}/names/approvals")

    get_response = api_client.get(
        f"/ct/terms/{new_term_uid}/names",
        params={"include_ts_parameters": True},
    )
    assert_response_status_code(get_response, 200)
    data = get_response.json()

    assert data["osb_field_name"] == "study_post_create_field"
    assert data["osb_page_reference"] == "p.7"
    assert data["semantic_data_type"]["uid"] == "DT_TEXT"
    assert data["response_codelist"]["uid"] == "CTCodelist_YesNo"
    assert [t["uid"] for t in data["valid_null_flavor_terms"]] == ["NF_NA"]
    assert data["reference"] == "ClinicalTrials.gov"
    assert data["required_level"] == "Required"
    assert data["cardinality"] == "One"
    assert data["notes"] == "Created via POST /ct/terms with ts_parameter."


def test_post_ct_term_without_ts_parameter_has_null_ts_properties(api_client):
    """POST /ct/terms without `ts_parameter` keeps existing behavior — all TS
    properties must be null on the resulting term."""
    create_response = api_client.post(
        "/ct/terms",
        json={
            "catalogue_names": ["SDTM CT"],
            "codelists": [
                {
                    "codelist_uid": "C66738",
                    "submission_value": "NOPARAMCREATE",
                    "order": 100,
                }
            ],
            "library_name": "Sponsor",
            "definition": "Term created without ts_parameter.",
            "sponsor_preferred_name": "No TS Param Term",
            "sponsor_preferred_name_sentence_case": "no ts param term",
        },
    )
    assert_response_status_code(create_response, 201)
    new_term_uid = create_response.json()["term_uid"]

    api_client.post(f"/ct/terms/{new_term_uid}/names/approvals")

    get_response = api_client.get(
        f"/ct/terms/{new_term_uid}/names",
        params={"include_ts_parameters": True},
    )
    assert_response_status_code(get_response, 200)
    data = get_response.json()

    assert data["osb_field_name"] is None
    assert data["osb_page_reference"] is None
    assert data["semantic_data_type"] is None
    assert data["response_codelist"] is None
    assert data["valid_null_flavor_terms"] in (None, [])
    assert data["reference"] is None
    assert data["required_level"] is None
    assert data["cardinality"] is None
    assert data["notes"] is None


# ---------- GET /meta-study-fields ----------


def test_get_meta_study_fields_lists_predefined_nodes(api_client):
    """`GET /meta-study-fields` returns each predefined MetaStudyField node
    with its `osb_field_name` and `osb_page_reference`."""
    # Set an osb_page_reference on the existing MSF (the one created by
    # patch_trial_summary_parameter on TS_TERM_UID), and create a second MSF
    # without an osb_page_reference so we cover both populated and null cases.
    db.cypher_query(
        "MATCH (msf:MetaStudyField {osb_field_name: 'study_short_title'}) "
        "SET msf.osb_page_reference = 'p.42'"
    )
    db.cypher_query("MERGE (:MetaStudyField {osb_field_name: 'another_meta_field'})")

    response = api_client.get("/meta-study-fields")
    assert_response_status_code(response, 200)
    items = response.json()

    assert isinstance(items, list)
    by_name = {item["osb_field_name"]: item for item in items}

    assert "study_short_title" in by_name
    assert by_name["study_short_title"]["osb_page_reference"] == "p.42"

    assert "another_meta_field" in by_name
    assert by_name["another_meta_field"]["osb_page_reference"] is None
