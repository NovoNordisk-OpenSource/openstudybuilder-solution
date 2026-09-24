"""
Tests for sponsor ct package
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
import urllib.parse
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
catalogue: str
cdisc_package_name: str
sponsor_package_name: str

URL = "/ct/packages"


@pytest.fixture(scope="function")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="function")
def test_data():
    """Initialize test data"""
    db_name = "sponsor-ct-packages.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_subset=False, inject_lock_unlock_codelists=False)
    TestUtils.create_study_fields_ct_data()

    global catalogue
    global cdisc_package_name
    global sponsor_package_name

    catalogue = "SDTM CT"
    cdisc_package_name = "SDTM CT 2020-03-27"

    TestUtils.create_ct_package(
        catalogue=catalogue,
        name=cdisc_package_name,
        approve_elements=False,
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )
    sponsor_package = TestUtils.create_sponsor_ct_package(
        extends_package=cdisc_package_name,
        effective_date=date.today(),
    )
    sponsor_package_name = sponsor_package.name

    yield


SPONSOR_CT_PACKAGES_FIELDS_ALL = [
    "uid",
    "catalogue_name",
    "name",
    "label",
    "description",
    "href",
    "registration_status",
    "source",
    "import_date",
    "effective_date",
    "author_username",
    "extends_package",
]

SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL = [
    "uid",
    "catalogue_name",
    "name",
    "import_date",
    "effective_date",
    "author_username",
    "extends_package",
]


def test_get_all_ct_packages(api_client):
    """Test get sponsor ct packages"""
    response = api_client.get(f"{URL}?standards_only=false")
    assert validate_all_packages_list(
        response,
        expected_sponsor_num=1,
        expected_sponsor_package_uid=sponsor_package_name,
    )


def test_get_sponsor_ct_packages(api_client):
    """Test get sponsor ct packages"""
    response = api_client.get(f"{URL}?sponsor_only=true")
    assert validate_sponsor_package_list(
        response, expected_num=1, expected_name=sponsor_package_name
    )


def test_get_standard_ct_packages(api_client):
    """Test get standard ct packages"""
    response = api_client.get(URL)
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) > 0
    for package in res:
        assert package["extends_package"] is None


def test_post_sponsor_ct_package(api_client):
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")
    # Create a new sponsor package with a pre-existing date
    # Expect it to fail as this is forbidden
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": date.today().strftime("%Y-%m-%d"),
        },
    )
    assert_response_status_code(response, 409)

    # Create a sponsor package with a new date
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
        },
    )
    res = response.json()
    log.info("Created Sponsor CT Package: %s", res)

    expected_package_name = (
        f"Sponsor {catalogue} {(date.today() - timedelta(days=1)).strftime('%Y-%m-%d')}"
    )
    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["uid"] == expected_package_name
    assert res["name"] == res["uid"]
    assert set(res.keys()) == set(SPONSOR_CT_PACKAGES_FIELDS_ALL)
    for key in SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL:
        assert res[key] is not None

    # Finally, test the package GET endpoints are returning the new package
    # Sponsor only
    get_sponsor_only_res = api_client.get(f"{URL}?sponsor_only=true")
    assert validate_sponsor_package_list(
        get_sponsor_only_res, expected_name=expected_package_name, expected_num=2
    )

    # Get all
    all_packages_res = api_client.get(f"{URL}?standards_only=false")
    assert validate_all_packages_list(
        all_packages_res,
        expected_sponsor_num=2,
        expected_sponsor_package_uid=expected_package_name,
    )


def test_post_sponsor_ct_package_with_custom_library_name(api_client):
    """Test creating a sponsor CT package with a custom library name"""
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")

    custom_library_name = "CustomSponsor"
    effective_date_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date_str,
            "library_name": custom_library_name,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    expected_package_name = f"{custom_library_name} {catalogue} {effective_date_str}"
    assert res["uid"] == expected_package_name
    assert res["name"] == expected_package_name
    assert res["description"] == (
        f"{custom_library_name} package for {cdisc_package_name}, as of {effective_date_str}"
    )


def test_post_sponsor_ct_package_default_library_name(api_client):
    """Test that omitting library_name uses the default 'Sponsor' prefix"""
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")

    effective_date_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date_str,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    expected_package_name = f"Sponsor {catalogue} {effective_date_str}"
    assert res["uid"] == expected_package_name
    assert res["name"] == expected_package_name


def test_post_sponsor_ct_package_different_libraries_same_date(api_client):
    """Test that two packages with different library names but the same date can coexist"""
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")

    effective_date_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Create package with default library name
    response1 = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date_str,
        },
    )
    assert_response_status_code(response1, 201)

    # Create package with a different library name on the same date
    response2 = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date_str,
            "library_name": "AnotherSponsor",
        },
    )
    assert_response_status_code(response2, 201)

    res1 = response1.json()
    res2 = response2.json()
    assert res1["uid"] != res2["uid"]
    assert res1["uid"] == f"Sponsor {catalogue} {effective_date_str}"
    assert res2["uid"] == f"AnotherSponsor {catalogue} {effective_date_str}"

    # Both appear in sponsor-only listing
    get_sponsor_only_res = api_client.get(f"{URL}?sponsor_only=true")
    assert_response_status_code(get_sponsor_only_res, 200)
    sponsor_packages = get_sponsor_only_res.json()
    sponsor_uids = [pkg["uid"] for pkg in sponsor_packages]
    assert res1["uid"] in sponsor_uids
    assert res2["uid"] in sponsor_uids


def test_post_sponsor_ct_package_duplicate_prevention(api_client):
    """Test that creating a duplicate Sponsor CT Package is prevented and returns 409 with clear error message"""
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")

    # Create first sponsor package
    effective_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date,
        },
    )
    assert_response_status_code(response, 201)
    first_package = response.json()

    # Attempt to create duplicate with same effective date
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date,
        },
    )
    assert_response_status_code(response, 409)
    error_response = response.json()
    assert "type" in error_response
    assert error_response["type"] == "AlreadyExistsException"
    assert "message" in error_response
    assert "sponsor" in error_response["message"].lower()
    assert "ctpackage" in error_response["message"].lower()
    assert "already exists" in error_response["message"].lower()

    # Verify only one package exists with this date
    all_packages = api_client.get(f"{URL}?sponsor_only=true").json()
    packages_with_date = [
        pkg for pkg in all_packages if pkg["effective_date"] == effective_date
    ]
    assert len(packages_with_date) == 1
    assert packages_with_date[0]["uid"] == first_package["uid"]


def test_post_sponsor_ct_package_error_message_clarity(api_client):
    """Test that error message is clear and user-friendly when attempting to create duplicate package"""
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")

    # Create first sponsor package with today's date
    effective_date = date.today().strftime("%Y-%m-%d")
    response = api_client.post(
        f"{URL}/sponsor",
        json={
            "extends_package": cdisc_package_name,
            "effective_date": effective_date,
        },
    )
    # This should fail because test_data fixture already creates one for today
    assert_response_status_code(response, 409)
    error_response = response.json()

    # Verify error message is clear
    assert "message" in error_response
    error_message = error_response["message"].lower()
    assert "sponsor" in error_message
    assert "ctpackage" in error_message or "ct package" in error_message
    assert "already exists" in error_message or "exists" in error_message
    assert "date" in error_message


def test_query_codelists_with_sponsor_package_robustness(api_client):
    """Defensive test: Verify that querying codelists with a sponsor package name works correctly"""
    db.cypher_query("CREATE CONSTRAINT FOR (p:CTPackage) REQUIRE (p.uid) IS NODE KEY")

    # Create a sponsor package
    effective_date = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    package = create_sponsor_package(api_client, effective_date)
    package_name = package["name"]

    # Query codelists with the sponsor package - should work without errors
    response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package_name)}&page_size=10&is_sponsor=true"
    )
    assert_response_status_code(response, 200)
    codelists_response = response.json()
    assert "items" in codelists_response
    assert isinstance(codelists_response["items"], list)

    # Verify the query doesn't throw MultipleNodesReturned error
    # (which would manifest as a 400 or 500 error)
    assert response.status_code in [200, 201]

    # Verify we can query terms as well
    response = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package_name)}&page_size=10&is_sponsor=true"
    )
    assert_response_status_code(response, 200)
    terms_response = response.json()
    assert "items" in terms_response
    assert isinstance(terms_response["items"], list)


def test_sponsor_ct_package_codelists_isolated_per_library(api_client):
    """Test that querying codelists for a sponsor package with a specific library_name
    only returns codelists from CDISC or that library, not from other editable libraries.
    """
    # Create a second editable library
    custom_library_name = "CustomSponsor"
    TestUtils.create_library(name=custom_library_name, is_editable=True)

    # Create a codelist in the custom library
    custom_codelist = TestUtils.create_ct_codelist(
        name=TestUtils.random_str(length=6, prefix="CustomCL"),
        library_name=custom_library_name,
        approve=True,
        effective_date=datetime.now() - timedelta(days=2),
    )

    # Create sponsor packages for both libraries
    effective_date_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    default_package = create_sponsor_package(api_client, effective_date_str)
    custom_package = create_sponsor_package(
        api_client, effective_date_str, library_name=custom_library_name
    )

    # Query codelists for the default Sponsor package, filtered to Sponsor library
    response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(default_package['name'])}"
        f"&page_size=0&is_sponsor=true&library_name=Sponsor"
    )
    assert_response_status_code(response, 200)
    default_codelists = response.json()["items"]
    assert len(default_codelists) > 0

    # Verify no codelist from CustomSponsor library is returned
    default_codelist_libraries = {cl["library_name"] for cl in default_codelists}
    assert custom_library_name not in default_codelist_libraries
    assert "Sponsor" in default_codelist_libraries
    assert custom_codelist.codelist_uid not in [
        cl["codelist_uid"] for cl in default_codelists
    ]

    # Query codelists for the custom package, filtered to CustomSponsor library
    response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(custom_package['name'])}"
        f"&page_size=0&is_sponsor=true&library_name={custom_library_name}"
    )
    assert_response_status_code(response, 200)
    custom_codelists = response.json()["items"]
    assert len(custom_codelists) > 0

    # Verify only CustomSponsor codelists are returned (not default Sponsor ones)
    custom_codelist_libraries = {cl["library_name"] for cl in custom_codelists}
    assert "Sponsor" not in custom_codelist_libraries
    assert custom_library_name in custom_codelist_libraries
    assert custom_codelist.codelist_uid in [
        cl["codelist_uid"] for cl in custom_codelists
    ]

    # Query codelists for the default package filtered to CDISC
    # should return only CDISC codelists from the parent package
    response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(default_package['name'])}"
        f"&page_size=0&is_sponsor=true&library_name=CDISC"
    )
    assert_response_status_code(response, 200)
    cdisc_codelists = response.json()["items"]
    assert len(cdisc_codelists) > 0
    cdisc_codelist_libraries = {cl["library_name"] for cl in cdisc_codelists}
    assert cdisc_codelist_libraries == {"CDISC"}


def test_get_codelists_sponsor_ct_package(api_client):
    package = create_sponsor_package(
        api_client, (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # Check that codelists have properly been attached to the package
    # First, get list of expected uids
    cdisc_package_codelists_uids, sponsor_codelists_uids = list_expected_codelist_uids(
        api_client, cdisc_package_name
    )
    # Now, list codelists for the sponsor package
    # It should contain both the codelists from parent CDISC package
    # As well as all of the sponsor codelists
    sponsor_package_codelists_response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    )
    sponsor_package_codelists_res = sponsor_package_codelists_response.json()
    assert sponsor_package_codelists_response.status_code == 200
    assert len(sponsor_package_codelists_res["items"]) > 0
    codelist_uids = [
        codelist["codelist_uid"] for codelist in sponsor_package_codelists_res["items"]
    ]
    assert set(cdisc_package_codelists_uids) <= set(codelist_uids)
    assert set(sponsor_codelists_uids) <= set(codelist_uids)
    assert len(cdisc_package_codelists_uids) + len(sponsor_codelists_uids) == len(
        codelist_uids
    )


def test_get_terms_sponsor_ct_package(api_client):
    package = create_sponsor_package(
        api_client, (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # Check that terms have properly been attached to the package
    # First, get list of expected uids
    cdisc_package_terms_uids, sponsor_terms_uids = list_expected_term_uids(
        api_client, cdisc_package_name
    )
    sponsor_package_terms_response = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    )
    sponsor_package_terms_res = sponsor_package_terms_response.json()
    assert sponsor_package_terms_response.status_code == 200
    assert len(sponsor_package_terms_res["items"]) > 0
    term_uids = [term["term_uid"] for term in sponsor_package_terms_res["items"]]
    assert set(cdisc_package_terms_uids) <= set(term_uids)
    assert set(sponsor_terms_uids) <= set(term_uids)
    assert len(set(cdisc_package_terms_uids + sponsor_terms_uids)) == len(
        set(term_uids)
    )


def test_get_codelists_identical_sponsor_ct_package_nochanges(api_client):
    package = create_sponsor_package(
        api_client, (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # When the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # is called to get codelists content of a Sponsor CT Package
    sponsor_package_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    ).json()["items"]

    # Then the API must return all codelists content related to a Sponsor CT Package
    # identical to the return from GET /ct/codelists
    all_codelists = api_client.get("ct/codelists?page_size=0").json()["items"]

    # Validate that all codelists in sponsor package are contained as is in the full list
    assert all(codelist in all_codelists for codelist in sponsor_package_codelists)


def test_get_terms_identical_sponsor_ct_package_nochanges(api_client):
    package = create_sponsor_package(
        api_client, (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    )

    # When the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # is called to get terms content of a Sponsor CT Package
    sponsor_package_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['name'])}&page_size=0&is_sponsor=true"
    ).json()["items"]

    # Then the API must return all terms content related to a Sponsor CT Package
    # identical to the return from GET /ct/terms
    all_terms = api_client.get("ct/terms?page_size=0").json()["items"]

    # Validate that all terms in sponsor package are contained as is in the full list
    assert all(term in all_terms for term in sponsor_package_terms)


def test_sponsor_ct_package_is_persistent_sponsor_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]

    # When the POST API endpoint /ct/codelists/ is called
    # to create a new Sponsor Codelist not related to the test Sponsor CT Package
    new_codelist = TestUtils.create_ct_codelist(
        name=TestUtils.random_str(length=6, prefix="CTCodelist"),
        library_name="Sponsor",
        approve=True,
        effective_date=datetime.now(),
    )

    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will not return the newly created Sponsor codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert new_codelist.codelist_uid not in [
        codelist["codelist_uid"] for codelist in updated_codelists
    ]


def test_sponsor_ct_package_is_persistent_sponsor_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    # Create a Sponsor codelist
    new_codelist = TestUtils.create_ct_codelist(
        name=TestUtils.random_str(length=6, prefix="CTCodelist"),
        library_name="Sponsor",
        approve=True,
        extensible=True,
        effective_date=datetime.now(),
    )

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]

    # When the POST API endpoint /ct/terms/ is called
    # to create a new Sponsor Term not related to the test Sponsor CT Package
    new_term = TestUtils.create_ct_term(
        codelist_uid=new_codelist.codelist_uid,
        library_name="Sponsor",
        effective_date=datetime.now(),
    )

    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will not return the newly created Sponsor term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert new_term.term_uid not in [term["term_uid"] for term in updated_terms]


def test_sponsor_ct_package_is_persistent_sponsor_name_cdisc_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    cdisc_codelist = next(
        (
            codelist
            for codelist in initial_codelists
            if codelist["library_name"] == "CDISC"
        ),
        None,
    )
    # When the PATCH API endpoint /ct/codelists/<Test CDISC Codelist uid>/names is called
    # to update sponsor name for a CDISC Codelist related to the test Sponsor CT Package
    new_name = "New CDISC name"
    api_client.patch(
        f"ct/codelists/{cdisc_codelist['codelist_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated CDISC codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert [x for x in updated_codelists if x not in initial_codelists] == []


def test_sponsor_ct_package_is_persistent_sponsor_name_sponsor_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_codelist = next(
        (
            codelist
            for codelist in initial_codelists
            if codelist["library_name"] == "Sponsor"
        ),
        None,
    )
    # When the PATCH API endpoint /ct/codelists/<Test Sponsor Codelist uid>/names is called
    # to update sponsor name for a Sponsor Codelist related to the test Sponsor CT Package
    new_name = "New Sponsor name"
    api_client.patch(
        f"ct/codelists/{sponsor_codelist['codelist_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated Sponsor codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert [x for x in updated_codelists if x not in initial_codelists] == []


def test_sponsor_ct_package_is_persistent_attributes_sponsor_codelists(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_codelist = next(
        (
            codelist
            for codelist in initial_codelists
            if codelist["library_name"] == "Sponsor"
        ),
        None,
    )
    # When the PATCH API endpoint /ct/codelists/<Test Sponsor Codelist uid>/attributes is called
    # to update attributes for a Sponsor Codelist related to the test Sponsor CT Package
    new_definition = "New definition"
    api_client.post(
        f"ct/codelists/{sponsor_codelist['codelist_uid']}/attributes/versions",
    )
    api_client.patch(
        f"ct/codelists/{sponsor_codelist['codelist_uid']}/attributes",
        json={"definition": new_definition},
    )
    # Then the call to the GET API endpoint /ct/codelists?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original attribute values
    # for the updated Sponsor codelist
    updated_codelists = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_codelists) == len(updated_codelists)
    assert [x for x in updated_codelists if x not in initial_codelists] == []


def test_sponsor_ct_package_is_persistent_sponsor_name_cdisc_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    cdisc_term = next(
        (term for term in initial_terms if term["library_name"] == "CDISC"),
        None,
    )
    # When the PATCH API endpoint /ct/terms/<Test CDISC Term uid>/names is called
    # to update sponsor name for a CDISC Term related to the test Sponsor CT Package
    new_name = "New CDISC name"
    api_client.patch(
        f"ct/terms/{cdisc_term['term_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated CDISC term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert [x for x in updated_terms if x not in initial_terms] == []


def test_sponsor_ct_package_is_persistent_sponsor_name_sponsor_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_term = next(
        (term for term in initial_terms if term["library_name"] == "Sponsor"),
        None,
    )
    # When the PATCH API endpoint /ct/terms/<Test Sponsor Term uid>/names is called
    # to update sponsor name for a Sponsor Term related to the test Sponsor CT Package
    new_name = "New Sponsor name"
    api_client.patch(
        f"ct/terms/{sponsor_term['term_uid']}/names",
        json={"name": new_name, "change_description": new_name},
    )
    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original sponsor name and name_sentence_case attribute value
    # for the updated Sponsor term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert [x for x in updated_terms if x not in initial_terms] == []


def test_sponsor_ct_package_is_persistent_attributes_sponsor_terms(api_client):
    # Given a Sponsor CT Package exist for a CT Catalogue related to a CDISC CT Package
    package = initialize_persistence_tests(api_client)

    initial_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    sponsor_term = next(
        (term for term in initial_terms if term["library_name"] == "Sponsor"),
        None,
    )
    # When the PATCH API endpoint /ct/terms/<Test Sponsor Term uid>/attributes is called
    # to update attributes for a Sponsor Term related to the test Sponsor CT Package
    new_definition = "New definition"
    api_client.post(
        f"ct/terms/{sponsor_term['term_uid']}/attributes/versions",
    )
    api_client.patch(
        f"ct/terms/{sponsor_term['term_uid']}/attributes",
        json={"definition": new_definition},
    )
    # Then the call to the GET API endpoint /ct/terms?package=<Test Sponsor CT Package>
    # with a reference to the test Sponsor CT Package will return the original attribute values
    # for the updated Sponsor term
    updated_terms = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(package['uid'])}&page_size=0&is_sponsor=True"
    ).json()["items"]
    assert len(initial_terms) == len(updated_terms)
    assert [x for x in updated_terms if x not in initial_terms] == []


def initialize_persistence_tests(api_client):
    # Create some older terms and codelists
    TestUtils.create_ct_package(
        number_of_codelists=2,
        catalogue=catalogue,
        name=cdisc_package_name + "_old",
        approve_elements=False,
        effective_date=datetime.now(timezone.utc) - timedelta(days=7),
    )

    # Create an older sponsor package, but more recent that the CDISC one
    package = create_sponsor_package(
        api_client, (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    )

    return package


# Utility methods
def create_sponsor_package(api_client, effective_date, library_name=None):
    body = {
        "extends_package": cdisc_package_name,
        "effective_date": effective_date,
    }
    if library_name is not None:
        body["library_name"] = library_name
    response = api_client.post(
        f"{URL}/sponsor",
        json=body,
    )
    res = response.json()
    log.info("Created Sponsor CT Package: %s", res)
    assert_response_status_code(response, 201)

    return res


def validate_all_packages_list(
    response, expected_sponsor_num, expected_sponsor_package_uid
):
    res = response.json()

    assert_response_status_code(response, 200)

    # Get package in res where extends_package is set
    sponsor_packages = [el for el in res if el["extends_package"] is not None]
    assert len(res) > len(sponsor_packages)
    assert len(sponsor_packages) == expected_sponsor_num

    # Check the expected uid is in the list and extract the package
    sponsor_package = next(
        (el for el in sponsor_packages if el["uid"] == expected_sponsor_package_uid),
        None,
    )
    assert sponsor_package

    # Check fields included in the response
    fields_all_set = set(SPONSOR_CT_PACKAGES_FIELDS_ALL)
    assert set(list(sponsor_package.keys())) == fields_all_set
    for key in SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL:
        assert sponsor_package[key] is not None

    assert sponsor_package["catalogue_name"] == catalogue
    assert sponsor_package["name"] == expected_sponsor_package_uid
    assert sponsor_package["extends_package"] == cdisc_package_name

    return True


def validate_sponsor_package_list(response, expected_name, expected_num):
    res = response.json()

    assert_response_status_code(response, 200)

    # Get package in res where extends_package is set
    sponsor_packages = [el for el in res if el["extends_package"] is not None]
    assert len(res) == len(sponsor_packages)
    assert len(sponsor_packages) == expected_num

    # Check fields included in the response
    fields_all_set = set(SPONSOR_CT_PACKAGES_FIELDS_ALL)
    assert set(list(sponsor_packages[0].keys())) == fields_all_set
    for key in SPONSOR_CT_PACKAGES_FIELDS_NOT_NULL:
        assert sponsor_packages[0][key] is not None

    assert sponsor_packages[0]["uid"] == expected_name
    assert sponsor_packages[0]["catalogue_name"] == catalogue
    assert sponsor_packages[0]["name"] == expected_name
    assert sponsor_packages[0]["extends_package"] == cdisc_package_name

    return True


def list_expected_codelist_uids(api_client, parent_package_uid):
    # Codelists in parent CDISC package
    cdisc_package_codelists_response = api_client.get(
        f"ct/codelists?package={urllib.parse.quote_plus(parent_package_uid)}&page_size=0"
    )
    cdisc_package_codelists_res = cdisc_package_codelists_response.json()
    cdisc_package_codelists_uids = [
        codelist["codelist_uid"] for codelist in cdisc_package_codelists_res["items"]
    ]

    # Sponsor codelists
    sponsor_codelists_response = api_client.get(
        "ct/codelists?library_name=Sponsor&page_size=0"
    )
    sponsor_codelists_res = sponsor_codelists_response.json()
    sponsor_codelists_uids = [
        codelist["codelist_uid"] for codelist in sponsor_codelists_res["items"]
    ]

    return cdisc_package_codelists_uids, sponsor_codelists_uids


def list_expected_term_uids(api_client, parent_package_uid):
    # Terms in parent CDISC package
    cdisc_package_terms_response = api_client.get(
        f"ct/terms?package={urllib.parse.quote_plus(parent_package_uid)}&page_size=0"
    )
    cdisc_package_terms_res = cdisc_package_terms_response.json()
    cdisc_package_terms_uids = [
        term["term_uid"] for term in cdisc_package_terms_res["items"]
    ]

    # Sponsor terms
    sponsor_terms_response = api_client.get("ct/terms?library_name=Sponsor&page_size=0")
    sponsor_terms_res = sponsor_terms_response.json()
    sponsor_terms_uids = [term["term_uid"] for term in sponsor_terms_res["items"]]

    return cdisc_package_terms_uids, sponsor_terms_uids
