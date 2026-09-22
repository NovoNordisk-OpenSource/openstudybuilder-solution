"""Module for shared fixtures and hooks"""

import allure
import pytest
from pytest_bdd import step

from utils.utils import (
    REPORT_COLUMNS,
    REPORT_FILE_PATH,
    ExpectedFailureException,
    api_get,
    check_exclusions_exist,
    get_db_connection,
    get_exclusion_details,
)

db = get_db_connection()


@pytest.fixture(scope="session")
def prepare_report_file():
    with open(REPORT_FILE_PATH, "w", encoding="UTF-8") as file:
        file.write(f"{','.join(REPORT_COLUMNS)}\n")
        file.close()


def pytest_runtest_setup(item):
    """
    Hook that runs before each test to add Allure labels and severity from pytest markers.
    Extracts @impact:* markers and adds them as:
    - Allure labels (for filtering)
    - Allure severity (for categorization in the severity section)
    Uses the same marker access pattern as get_gherkin_tags().
    """
    # Mapping impact tags to Allure severity levels
    IMPACT_TO_SEVERITY = {
        "data_schema": allure.severity_level.CRITICAL,
        "business_rules": allure.severity_level.CRITICAL,
        "performance": allure.severity_level.NORMAL,
        "library_quality": allure.severity_level.MINOR,
        "api": allure.severity_level.NORMAL,
        "consumer_api": allure.severity_level.NORMAL,
        "api_soa": allure.severity_level.NORMAL,
    }

    severity_set = False

    # Use own_markers (same as get_gherkin_tags) to access markers from feature files
    for marker in item.own_markers:
        marker_name = marker.name
        # Handle markers with colon syntax like @impact:data_schema
        if ":" in marker_name:
            key, value = marker_name.split(":", 1)
            if key == "impact":
                tag_value = value.strip()
                # Add impact tag as Allure label (using impact_tags to match CSV column name)
                allure.dynamic.label("impact_tags", tag_value)
                # Add impact tag as epic (for grouping in Allure report - epics appear in their own section)
                allure.dynamic.epic(tag_value)

                # Map impact tag to severity level
                if not severity_set and tag_value in IMPACT_TO_SEVERITY:
                    allure.dynamic.severity(IMPACT_TO_SEVERITY[tag_value])
                    severity_set = True
                elif not severity_set:
                    # Default severity for unknown impact tags
                    allure.dynamic.severity(allure.severity_level.NORMAL)
                    severity_set = True
            elif key == "REQ_ID":
                req_id = value.strip()
                # Add requirement ID as Allure label
                allure.dynamic.label("requirement", req_id)

    # If no impact tags found, set default severity to MINOR
    if not severity_set:
        allure.dynamic.severity(allure.severity_level.MINOR)


@step("the API is reachable")
def api_reachable():
    api_get(path="/system/healthcheck")


@step("the database is reachable and has content")
def some_nodes_exist():
    query = """
        MATCH (n)
        RETURN count(n)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@step("the list of all studies with their versions is retrieved")
def db_get_list_of_studies_with_versions():
    query = """
        MATCH (sr:StudyRoot)-[hv:HAS_VERSION]->(sv:StudyValue)
        MATCH (sr_deleted:StudyRoot)-[:LATEST]->(:StudyValue)<-[:BEFORE]-(:Delete)
        WITH collect(DISTINCT sr_deleted.uid) AS deleted_uids, sr, hv, sv        
        WHERE not sr.uid in deleted_uids
        WITH DISTINCT sr.uid as uid, [item IN collect(hv) | {number: item.version, status: item.status}] AS versions
        RETURN uid, apoc.coll.toSet([v IN versions WHERE v.number IS NOT NULL | v.number]) AS version_numbers
        ORDER BY uid
    """
    response, _ = db.cypher_query(query)

    # Return a list of tuples (study_uid, [list_of_versions])
    ret = [(study[0], study[1]) for study in response]
    return ret


@step("the list of studies is retrieved")
def api_get_studies():
    url = "/v1/studies"
    res = api_get(
        path=url, params={"page_size": 1000, "sort_by": "uid"}, consumer_api=True
    )

    studies = [study["uid"] for study in res.json()["items"]]
    print(f"STUDIES: {studies}")
    return studies


def get_check_id_from_test_item(item) -> str:
    """
    Extract check_id from pytest test item.
    Works for both regular pytest tests and pytest-bdd scenarios.

    Args:
        item: pytest test item

    Returns:
        Test function name as check_id, or empty string if not available
    """
    if hasattr(item, "function") and hasattr(item.function, "__name__"):
        return item.function.__name__
    return ""


def _get_exception_type(call):
    """
    Extract exception type from pytest call object.

    Args:
        call: pytest call object

    Returns:
        Exception type or None if not found
    """
    if not hasattr(call, "excinfo") or call.excinfo is None:
        return None

    # Try different ways to get exception type
    if hasattr(call.excinfo, "type"):
        return call.excinfo.type
    if hasattr(call.excinfo, "value") and call.excinfo.value:
        return type(call.excinfo.value)
    if isinstance(call.excinfo, tuple) and len(call.excinfo) >= 1:
        return call.excinfo[0]
    return None


def _get_exception_name(exc_type, call):
    """
    Get human-readable exception name.

    Args:
        exc_type: Exception type
        call: pytest call object

    Returns:
        Exception name as string
    """
    exc_name = exc_type.__name__ if hasattr(exc_type, "__name__") else str(exc_type)
    # Get more specific exception name if available
    if hasattr(call, "excinfo") and call.excinfo is not None:
        if hasattr(call.excinfo, "value") and call.excinfo.value:
            exc_name = type(call.excinfo.value).__name__
    return exc_name


def _handle_non_assertion_error(call, exc_type):
    """
    Handle non-AssertionError exceptions by adding BROKEN status description to Allure.

    Args:
        call: pytest call object
        exc_type: Exception type
    """
    exc_name = _get_exception_name(exc_type, call)
    description = (
        "<p><strong>Test defect detected (BROKEN status).</strong></p>"
        "<p>This test failed due to a test infrastructure issue (e.g., database query error, "
        "network timeout, connection problem) rather than a product defect. The exception type was: "
        f"<code>{exc_name}</code></p>"
    )
    allure.dynamic.description_html(description)


def _handle_exclusions_for_failed_test(check_id):
    """
    Add exclusion details to Allure description for failed tests with exclusions.

    Args:
        check_id: Test check identifier
    """
    exclusion_details = get_exclusion_details(check_id)
    description = (
        "<p><strong>Test failed with exclusions present.</strong></p>"
        "<p>Note: This test has known exclusions, but the failure indicates a real issue.</p>"
        f"<pre>{exclusion_details}</pre>"
    )
    allure.dynamic.description_html(description)


def pytest_itemcollected(item):
    """
    Formats the test names insde the test report based on test method docstrings,
    which allows the report to contain more meaningful text than just the test method name.
    This will also format the docstring using the test parameters values.
    """
    # pylint: disable=protected-access
    node = item.obj
    test_docstring = node.__doc__.strip() if node.__doc__ else None
    if test_docstring:
        # Check if the test item has a `pytest.param` value,
        # and format the test docstring using the supplied parameter values
        if hasattr(item, "callspec") and hasattr(item.callspec, "params"):
            params = list(item.callspec.params.values())
            test_docstring = test_docstring.format(*params)
        item._nodeid = f"{item._nodeid} \t {test_docstring}"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Hook called after test execution to modify test report based on exclusions.

    Handles:
    - ExpectedFailureException (all violations excluded by EXCLUDED_NODE_IDS) -> pass + Allure note
    - Other non-AssertionError exceptions (infra errors) -> BROKEN Allure description
    - Tests with exclusions that still failed -> Add exclusion context to Allure
    """
    # Yield to get the report object
    outcome = yield
    report = outcome.get_result()
    if call.when != "call":  # Only process actual test execution
        return

    # All DB violations were filtered by EXCLUDED_NODE_IDS -> pass pytest (not a product failure)
    if (
        report.outcome == "failed"
        and call.excinfo is not None
        and call.excinfo.errisinstance(ExpectedFailureException)
    ):
        report.outcome = "passed"
        report.longrepr = None
        allure.dynamic.description_html(
            "<p><strong>Known exclusions only.</strong></p>"
            "<p>Every reported failure is covered by configured exclusions. "
            "This is not treated as a failing assertion.</p>"
            f"<pre>{call.excinfo.value}</pre>"
        )
        return

    check_id = get_check_id_from_test_item(item)

    # Check if test failed due to non-AssertionError (test defect, not product defect)
    if report.outcome == "failed":
        exc_type = _get_exception_type(call)
        if exc_type and exc_type not in (AssertionError, ExpectedFailureException):
            _handle_non_assertion_error(call, exc_type)

    # Handle tests with exclusions
    if check_id and check_exclusions_exist(check_id) and report.outcome == "failed":
        _handle_exclusions_for_failed_test(check_id)
