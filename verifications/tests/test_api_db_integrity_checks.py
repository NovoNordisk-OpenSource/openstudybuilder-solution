"""
DB integrity: run all checks defined in clinical-mdr-api ``db_integrity_checks.QUERIES``.
"""

# pylint: disable=unused-argument

import os

from pytest_bdd import scenarios, then

from utils.integrity_checks_support import (
    fail_if_integrity_errors,
    run_all_api_integrity_checks,
)
from utils.utils import REPORT_FILE_PATH, get_db_connection, get_logger

scenarios("studies/api_db_integrity.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@then("all API database integrity checks pass for non-deleted studies")
def all_api_db_integrity_checks_pass(prepare_report_file):
    """Execute every API integrity query for each non-deleted study; fail with CSV + Allure context."""
    failures = run_all_api_integrity_checks(db, REPORT_FILE_PATH)
    if failures:
        logger.warning("Integrity failures: %s", failures)
    fail_if_integrity_errors(failures, REPORT_FILE_PATH)
