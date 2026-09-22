# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
"""
Integration tests for `GET /v1/papillons/non-standard-variables` and the
SEMTCDT -> NSVXMLDT (NSV XML Data Type) data type translation it relies on.

All fixtures below are created through the real domain services (via
`TestUtils`), not sampled from ambient/pre-seeded data - each assertion
checks a value against inputs this module itself created, including a
dedicated SEMTCDT/NSVXMLDT codelist pair and IS_SPECIALIZATION_OF chain, so
the tests are deterministic regardless of what else is in the database.
"""

import csv
import io
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassRelInput,
    CTTermRef,
    NonStandardVariableInput,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db
from consumer_api.v1 import db as DB

ENDPOINT = "/v1/papillons/non-standard-variables"
MAPPING_ENDPOINT = "/v1/papillons/data-type-mapping"

EXPECTED_COLUMNS = [
    "cd_list_id",
    "cd_val",
    "cd_val_lb",
    "cd_val_short_lb",
    "cd_val_desc",
    "sdtm_qnam_data_type",
    "sdtm_qnam_length",
    "sdtm_qnam_ct",
    "sdtm_qnam_algorithm",
    "sdtm_qnam_multiple",
    "sdtm_qnam_qorig",
    "cd_val_std",
    "cd_list_val_status",
]

# Data type submission value shared by every NSV below - it is a 0-hop
# NSVXMLDT term (i.e. it is tagged NSVXMLDT directly), it doesn't test the
# multi-hop traversal. `dt_two_hop` (below) covers the >0 hop case.
NSV_XML_DT_LEAF_SUBMISSION_VALUE = "papillons_test_leaf"
NSV_XML_DT_TWO_HOP_SUBMISSION_VALUE = "papillons_test_two_hop"

# Non-standard variables created by `test_data`, keyed by `code` (== cd_val),
# each with the exact expected export row values.
NSV1_ASSIGNED = "PAPILLONS_TEST_NSV_ASSIGNED"
NSV2_CRF_ZERO_LENGTH = "PAPILLONS_TEST_NSV_CRF_ZERO_LENGTH"
NSV3_DERIVED = "PAPILLONS_TEST_NSV_DERIVED"
NSV4_EDT = "PAPILLONS_TEST_NSV_EDT"
NSV5_NO_ORIGIN_MAPPING = "PAPILLONS_TEST_NSV_NO_ORIGIN_MAPPING"
NSV6_DRAFT_EXCLUDED = "PAPILLONS_TEST_NSV_DRAFT_EXCLUDED"

EXPECTED_ROWS_BY_CODE: dict[str, dict[str, Any]] = {
    NSV1_ASSIGNED: {
        "cd_val_lb": "Papillons Test NSV Assigned",
        "cd_val_desc": "Definition of the Assigned-origin test NSV",
        "sdtm_qnam_data_type": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
        "sdtm_qnam_length": "10",
        "sdtm_qnam_algorithm": "ALGORITHM_ASSIGNED",
        "sdtm_qnam_multiple": "Y",
        "sdtm_qnam_qorig": "Assigned",
        "cd_val_std": "Y",
    },
    NSV2_CRF_ZERO_LENGTH: {
        "cd_val_lb": "Papillons Test NSV CRF Zero Length",
        "cd_val_desc": "",
        "sdtm_qnam_data_type": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
        "sdtm_qnam_length": "0",
        "sdtm_qnam_algorithm": "",
        "sdtm_qnam_multiple": "N",
        "sdtm_qnam_qorig": "CRF",
        "cd_val_std": "N",
    },
    NSV3_DERIVED: {
        "cd_val_lb": "Papillons Test NSV Derived",
        "cd_val_desc": "",
        "sdtm_qnam_data_type": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
        "sdtm_qnam_length": "5",
        "sdtm_qnam_algorithm": "",
        "sdtm_qnam_multiple": "N",
        "sdtm_qnam_qorig": "Derived",
        "cd_val_std": "N",
    },
    NSV4_EDT: {
        "cd_val_lb": "Papillons Test NSV eDT",
        "cd_val_desc": "",
        "sdtm_qnam_data_type": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
        "sdtm_qnam_length": "20",
        "sdtm_qnam_algorithm": "",
        "sdtm_qnam_multiple": "N",
        "sdtm_qnam_qorig": "eDT",
        "cd_val_std": "N",
    },
    NSV5_NO_ORIGIN_MAPPING: {
        "cd_val_lb": "Papillons Test NSV No Origin Mapping",
        "cd_val_desc": "",
        "sdtm_qnam_data_type": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
        "sdtm_qnam_length": "15",
        "sdtm_qnam_algorithm": "",
        "sdtm_qnam_multiple": "N",
        "sdtm_qnam_qorig": "",
        "cd_val_std": "N",
    },
}


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client using the database name set in `test_data`."""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """
    Creates a self-contained SEMTCDT/NSVXMLDT codelist pair with an
    IS_SPECIALIZATION_OF chain, origin type/source terms matching
    `_MMA_QORIG_REVERSE_MAP` in `v1/main.py`, and 5 Final Non-Standard
    Variables (plus 1 Draft one, to test the Final-only filter) covering
    every MMA QORIG mapping, the `length=0` edge case, and a >0 hop
    SEMTCDT -> NSVXMLDT resolution.
    """
    set_db("consumer-api-v1-papillons-nsv")
    inject_base_data()

    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Papillons Test Activity Instance Class"
    )
    assert activity_instance_class.uid is not None
    aic_rel = ActivityInstanceClassRelInput(
        uid=activity_instance_class.uid,
        mandatory=True,
        is_adam_param_specific_enabled=False,
        is_additional_optional=False,
        is_default_linked=False,
    )

    role_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test Role",
        submission_value="PAPILLONS_TEST_ROLE",
        extensible=True,
        approve=True,
    )
    role_term = TestUtils.create_ct_term(
        codelist_uid=role_codelist.codelist_uid,
        sponsor_preferred_name="Papillons Test Role Term",
    )
    # `ActivityItemClassRepository._get_or_create_value` also unconditionally
    # resolves every activity item class's role term into the legacy "ROLE"
    # codelist (`settings.stdm_role_cl_submval`), so `role_term` must be a
    # member of it too.
    legacy_role_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test Legacy Role",
        submission_value="ROLE",
        extensible=True,
        approve=True,
    )
    CTCodelistService().add_term(
        codelist_uid=legacy_role_codelist.codelist_uid,
        term_uid=role_term.term_uid,
        order=1,
        submission_value=role_term.codelists[0].submission_value,
    )

    # SEMTCDT and NSVXMLDT codelists, isolated from any ambient data.
    semtcdt_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test SEMTCDT",
        submission_value="SEMTCDT",
        extensible=True,
        approve=True,
    )
    nsv_xml_dt_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test NSVXMLDT",
        submission_value="NSVXMLDT",
        extensible=True,
        approve=True,
    )
    scratch_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test Scratch",
        submission_value="PAPILLONS_TEST_SCRATCH",
        extensible=True,
        approve=True,
    )
    # `ActivityItemClassRepository._get_or_create_value` (unrelated to the
    # SEMTCDT/NSVXMLDT mechanism under test) unconditionally resolves every
    # activity item class's data type term into the legacy "DATATYPE"
    # codelist (`settings.ddf_data_type_cl_submval`), so any term used as a
    # `data_type_uid` below must also be a member of it.
    data_type_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test DATATYPE",
        submission_value="DATATYPE",
        extensible=True,
        approve=True,
    )

    # 0-hop term: a SEMTCDT term that is itself also tagged NSVXMLDT.
    dt_leaf = TestUtils.create_ct_term(
        codelist_uid=semtcdt_codelist.codelist_uid,
        submission_value=NSV_XML_DT_LEAF_SUBMISSION_VALUE,
        sponsor_preferred_name="Papillons Test Leaf Data Type",
    )
    CTCodelistService().add_term(
        codelist_uid=nsv_xml_dt_codelist.codelist_uid,
        term_uid=dt_leaf.term_uid,
        order=1,
        submission_value=NSV_XML_DT_LEAF_SUBMISSION_VALUE,
    )
    CTCodelistService().add_term(
        codelist_uid=data_type_codelist.codelist_uid,
        term_uid=dt_leaf.term_uid,
        order=1,
        submission_value=NSV_XML_DT_LEAF_SUBMISSION_VALUE,
    )

    # Intermediate, untagged ancestor term (not a member of SEMTCDT or
    # NSVXMLDT - mirrors "string" sitting between "code" and "text" in the
    # real datatype.csv chain).
    dt_mid = TestUtils.create_ct_term(
        codelist_uid=scratch_codelist.codelist_uid,
        submission_value="papillons_test_mid",
        sponsor_preferred_name="Papillons Test Mid Data Type",
    )

    # 2-hop term: a SEMTCDT term whose NSVXMLDT ancestor is 2 IS_SPECIALIZATION_OF
    # hops away (dt_two_hop -> dt_mid -> dt_leaf).
    dt_two_hop = TestUtils.create_ct_term(
        codelist_uid=semtcdt_codelist.codelist_uid,
        submission_value=NSV_XML_DT_TWO_HOP_SUBMISSION_VALUE,
        sponsor_preferred_name="Papillons Test Two-Hop Data Type",
    )
    CTCodelistService().add_term(
        codelist_uid=data_type_codelist.codelist_uid,
        term_uid=dt_two_hop.term_uid,
        order=2,
        submission_value=NSV_XML_DT_TWO_HOP_SUBMISSION_VALUE,
    )
    TestUtils.add_ct_term_parent(
        term=dt_two_hop, parent=dt_mid, relationship_type="specialization"
    )
    TestUtils.add_ct_term_parent(
        term=dt_mid, parent=dt_leaf, relationship_type="specialization"
    )

    # Origin type/source terms whose sponsor preferred names match the keys
    # of `_MMA_QORIG_REVERSE_MAP` in `v1/main.py`.
    origin_type_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test Origin Type",
        submission_value="PAPILLONS_TEST_ORIGIN_TYPE",
        extensible=True,
        approve=True,
    )
    origin_source_codelist = TestUtils.create_ct_codelist(
        name="Papillons Test Origin Source",
        submission_value="PAPILLONS_TEST_ORIGIN_SOURCE",
        extensible=True,
        approve=True,
    )
    origin_type_terms = {
        name: TestUtils.create_ct_term(
            codelist_uid=origin_type_codelist.codelist_uid,
            sponsor_preferred_name=name,
        )
        for name in ("Assigned Value", "Collected Value", "Derived Value")
    }
    origin_source_terms = {
        name: TestUtils.create_ct_term(
            codelist_uid=origin_source_codelist.codelist_uid,
            sponsor_preferred_name=name,
        )
        for name in ("Clinical Study Sponsor", "Investigator", "Vendor")
    }

    def _origin_ref(terms_by_name, codelist, name) -> CTTermRef:
        return CTTermRef(
            term_uid=terms_by_name[name].term_uid,
            codelist_uid=codelist.codelist_uid,
        )

    order = 1

    def _create_nsv(
        code: str,
        display_name: str,
        data_type_uid: str,
        length: int,
        is_multiple: bool = False,
        is_cdisc_defined: bool = False,
        algorithm: str | None = None,
        definition: str | None = None,
        origin_type_name: str | None = None,
        origin_source_name: str | None = None,
        approve: bool = True,
    ):
        nonlocal order
        order += 1
        origin_type = (
            _origin_ref(origin_type_terms, origin_type_codelist, origin_type_name)
            if origin_type_name
            else None
        )
        origin_source = (
            _origin_ref(origin_source_terms, origin_source_codelist, origin_source_name)
            if origin_source_name
            else None
        )
        return TestUtils.create_activity_item_class(
            name=code,
            display_name=display_name,
            definition=definition,
            order=order,
            activity_instance_classes=[aic_rel],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_uid,
            non_standard_variable=NonStandardVariableInput(
                code=code,
                is_multiple=is_multiple,
                length=length,
                algorithm=algorithm,
                is_cdisc_defined=is_cdisc_defined,
                origin_type=origin_type,
                origin_source=origin_source,
            ),
            approve=approve,
        )

    _create_nsv(
        NSV1_ASSIGNED,
        display_name="Papillons Test NSV Assigned",
        definition="Definition of the Assigned-origin test NSV",
        data_type_uid=dt_leaf.term_uid,
        length=10,
        is_multiple=True,
        is_cdisc_defined=True,
        algorithm="ALGORITHM_ASSIGNED",
        origin_type_name="Assigned Value",
        origin_source_name="Clinical Study Sponsor",
    )
    _create_nsv(
        NSV2_CRF_ZERO_LENGTH,
        display_name="Papillons Test NSV CRF Zero Length",
        data_type_uid=dt_two_hop.term_uid,
        length=0,
        origin_type_name="Collected Value",
        origin_source_name="Investigator",
    )
    _create_nsv(
        NSV3_DERIVED,
        display_name="Papillons Test NSV Derived",
        data_type_uid=dt_leaf.term_uid,
        length=5,
        origin_type_name="Derived Value",
        origin_source_name="Clinical Study Sponsor",
    )
    _create_nsv(
        NSV4_EDT,
        display_name="Papillons Test NSV eDT",
        data_type_uid=dt_leaf.term_uid,
        length=20,
        origin_type_name="Collected Value",
        origin_source_name="Vendor",
    )
    _create_nsv(
        NSV5_NO_ORIGIN_MAPPING,
        display_name="Papillons Test NSV No Origin Mapping",
        data_type_uid=dt_two_hop.term_uid,
        length=15,
    )
    # Left in Draft status - must not appear in the (Final-only) export.
    _create_nsv(
        NSV6_DRAFT_EXCLUDED,
        display_name="Papillons Test NSV Draft Excluded",
        data_type_uid=dt_leaf.term_uid,
        length=1,
        approve=False,
    )

    return {
        "dt_leaf": dt_leaf,
        "dt_mid": dt_mid,
        "dt_two_hop": dt_two_hop,
    }


@pytest.fixture(scope="module")
def csv_rows(api_client: TestClient, test_data) -> list[dict[str, str]]:
    """Fetch the full CSV export once for the module and parse it into dicts."""
    response = api_client.get(ENDPOINT)
    assert_response_status_code(response, 200)
    assert response.headers["content-type"].startswith("text/csv")
    reader = csv.DictReader(io.StringIO(response.text), delimiter="|")
    return list(reader)


@pytest.fixture(scope="module")
def rows_by_code(csv_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["cd_val"]: row for row in csv_rows}


def test_response_is_csv_with_expected_header(api_client: TestClient, test_data):
    """The endpoint returns a CSV with the exact MMA SDTM_QNAM column set."""
    response = api_client.get(ENDPOINT)
    assert_response_status_code(response, 200)
    header_line = response.text.splitlines()[0]
    assert header_line.split("|") == EXPECTED_COLUMNS


def test_export_contains_exactly_the_created_final_nsvs(
    rows_by_code: dict[str, dict[str, str]],
):
    """
    Every Final NSV created by `test_data` appears exactly once, and the
    Draft NSV (created to test the Final-only filter) does not appear at all.
    """
    for code in EXPECTED_ROWS_BY_CODE:
        assert code in rows_by_code, f"Final NSV {code!r} missing from export"

    assert (
        NSV6_DRAFT_EXCLUDED not in rows_by_code
    ), "Draft NSV must be excluded from the (Final-only) Papillons export"


@pytest.mark.parametrize("code", list(EXPECTED_ROWS_BY_CODE))
def test_row_matches_exact_expected_values(
    rows_by_code: dict[str, dict[str, str]], code: str
):
    """
    Each created NSV's export row matches exactly the values it was created
    with - qorig mapping, length passthrough (including `length=0`), and
    the resolved NSVXMLDT data type - not just "is shaped correctly".
    """
    row = rows_by_code[code]
    expected = EXPECTED_ROWS_BY_CODE[code]

    assert row["cd_list_id"] == "SDTM_QNAM"
    assert row["cd_val"] == code
    assert row["cd_val_lb"] == expected["cd_val_lb"]
    assert row["cd_val_short_lb"] == expected["cd_val_lb"]
    assert row["cd_val_desc"] == expected["cd_val_desc"]
    assert row["sdtm_qnam_data_type"] == expected["sdtm_qnam_data_type"]
    assert row["sdtm_qnam_length"] == expected["sdtm_qnam_length"]
    assert row["sdtm_qnam_algorithm"] == expected["sdtm_qnam_algorithm"]
    assert row["sdtm_qnam_multiple"] == expected["sdtm_qnam_multiple"]
    assert row["sdtm_qnam_qorig"] == expected["sdtm_qnam_qorig"]
    assert row["cd_val_std"] == expected["cd_val_std"]
    assert row["cd_list_val_status"] == "A"


def test_zero_length_nsv_is_not_collapsed_to_empty_string(
    rows_by_code: dict[str, dict[str, str]],
):
    """
    Regression test: `sdtm_qnam_length` must round-trip `length=0` as `"0"`,
    not collapse it to `""` (which is reserved for "no length set").
    """
    assert rows_by_code[NSV2_CRF_ZERO_LENGTH]["sdtm_qnam_length"] == "0"


def test_unmapped_origin_pair_resolves_to_empty_qorig(
    rows_by_code: dict[str, dict[str, str]],
):
    """An NSV with no origin type/source set has an empty `sdtm_qnam_qorig`."""
    assert rows_by_code[NSV5_NO_ORIGIN_MAPPING]["sdtm_qnam_qorig"] == ""


def test_semtcdt_to_nsv_xml_dt_traversal_zero_hop(test_data):
    """A SEMTCDT term that is itself NSVXMLDT-tagged resolves to itself (0 hops)."""
    resolved = DB.get_nsv_xml_data_type_for_semtcdt_term(
        NSV_XML_DT_LEAF_SUBMISSION_VALUE
    )
    assert resolved == NSV_XML_DT_LEAF_SUBMISSION_VALUE


def test_semtcdt_to_nsv_xml_dt_traversal_two_hops(test_data):
    """
    A SEMTCDT term resolves to its NSVXMLDT ancestor 2 IS_SPECIALIZATION_OF
    hops away, not just the trivial same-term case.
    """
    resolved = DB.get_nsv_xml_data_type_for_semtcdt_term(
        NSV_XML_DT_TWO_HOP_SUBMISSION_VALUE
    )
    assert resolved == NSV_XML_DT_LEAF_SUBMISSION_VALUE


def test_unknown_semtcdt_term_resolves_to_none(test_data):
    """A submission value that isn't a real SEMTCDT term resolves to None."""
    assert DB.get_nsv_xml_data_type_for_semtcdt_term("not-a-real-semtcdt-term") is None


def test_data_type_mapping_endpoint_resolves_known_terms(
    api_client: TestClient, test_data
):
    """
    `GET /papillons/data-type-mapping/{semtcdt_term}` exposes the same
    IS_SPECIALIZATION_OF traversal as the CSV export's data type column,
    for both the 0-hop and 2-hop cases created above.
    """
    response = api_client.get(f"{MAPPING_ENDPOINT}/{NSV_XML_DT_LEAF_SUBMISSION_VALUE}")
    assert_response_status_code(response, 200)
    assert response.json() == {
        "semtcdt_term": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
        "nsv_xml_term": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
    }

    response = api_client.get(
        f"{MAPPING_ENDPOINT}/{NSV_XML_DT_TWO_HOP_SUBMISSION_VALUE}"
    )
    assert_response_status_code(response, 200)
    assert response.json() == {
        "semtcdt_term": NSV_XML_DT_TWO_HOP_SUBMISSION_VALUE,
        "nsv_xml_term": NSV_XML_DT_LEAF_SUBMISSION_VALUE,
    }


def test_data_type_mapping_endpoint_unknown_term_returns_null(api_client: TestClient):
    """An unrecognized SEMTCDT term maps to `nsv_xml_term: null`, not a 404/500."""
    response = api_client.get(f"{MAPPING_ENDPOINT}/not-a-real-semtcdt-term")
    assert_response_status_code(response, 200)
    body = response.json()
    assert body == {"semtcdt_term": "not-a-real-semtcdt-term", "nsv_xml_term": None}
