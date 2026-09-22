# pylint: disable=unused-argument,redefined-outer-name

import logging
import time
from typing import NamedTuple
from urllib.parse import urljoin

import neo4j.exceptions
import pytest
from neomodel import db

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCatalogue,
    Library,
)
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.tests.integration.utils.data_library import (
    create_reason_for_lock_unlock_terms,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import (
    SPONSOR_LIBRARY_NAME,
    TestUtils,
)
from clinical_mdr_api.tests.utils.utils import get_db_name
from common.config import settings
from common.database import configure_database

__all__ = ["temp_database", "base_data", "temp_database_populated"]


log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def temp_database(request) -> str:
    """module fixture to run tests with a temporary database, name derived from test module name"""

    # this import results to cypher queries which I don't want to run on the default database
    from clinical_mdr_api.routers.admin import clear_caches

    db_name = get_db_name(request.module.__name__)
    log.info(
        "%s fixture: using temporary database: %s",
        request.fixturename,
        db_name,
    )

    log.debug(
        "%s fixture: create or replace database: %s",
        request.fixturename,
        db_name,
    )

    # Switch to "neo4j" database for creating a new database
    driver = configure_database(
        urljoin(settings.neo4j_dsn, "/neo4j"),
        max_connection_lifetime=settings.neo4j_connection_lifetime,
        liveness_check_timeout=settings.neo4j_liveness_check_timeout,
    )
    db.set_connection(driver=driver)
    db.cypher_query("CREATE OR REPLACE DATABASE $db", {"db": db_name})

    log.debug(
        "%s fixture: altering database configuration to: %s",
        request.fixturename,
        db_name,
    )
    driver = configure_database(
        urljoin(settings.neo4j_dsn, f"/{db_name}"),
        max_connection_lifetime=settings.neo4j_connection_lifetime,
        liveness_check_timeout=settings.neo4j_liveness_check_timeout,
    )

    try_cnt = 1
    db_available = False
    while try_cnt < 10 and not db_available:
        try:
            # Database creation can take a couple of seconds
            # db.set_connection will return a ClientError if the database isn't ready
            # This allows for retrying after a small pause
            db.set_connection(driver=driver)

            try_cnt = try_cnt + 1
            db.cypher_query(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Counter) REQUIRE (c.counterId) IS NODE KEY"
            )
            db_available = True

        except (
            neo4j.exceptions.ClientError,
            neo4j.exceptions.DatabaseUnavailable,
        ) as exc:
            log.debug(
                "%s fixture: database '%s' not available, %s, pausing for 2 seconds",
                request.fixturename,
                db_name,
                exc.code,
            )
            time.sleep(2)

    if not db_available:
        log.info(
            "%s fixture: database '%s' not available, given up after %s tries",
            request.fixturename,
            db_name,
            try_cnt,
        )
        raise RuntimeError(f"db {db_name} is not available")

    # clear cached data after switching databases
    clear_caches()
    TestUtils.create_dummy_user()

    yield db_name

    log.debug(
        "%s fixture: reset to database configuration: %s",
        request.fixturename,
        settings.neo4j_dsn or settings.neo4j_database,
    )
    driver = configure_database(
        urljoin(settings.neo4j_dsn, "/neo4j"),
        max_connection_lifetime=settings.neo4j_connection_lifetime,
        liveness_check_timeout=settings.neo4j_liveness_check_timeout,
    )
    db.set_connection(driver=driver)

    # clear cached data after switching databases
    clear_caches()

    # Drop test database if pytest was not called with --keep-db command-line option
    if not request.config.getoption("--keep-db"):
        log.debug(
            "%s fixture: drop database: %s",
            request.fixturename,
            db_name,
        )
        db.cypher_query("DROP DATABASE $db IF EXISTS", {"db": db_name})


@pytest.fixture(scope="module")
def base_data(request, temp_database):
    """injects generic base data into a temporary database"""

    log.info("%s: injecting base data: inject_base_data()", request.fixturename)
    _, test_data_dict = inject_base_data()
    return test_data_dict


class TempDatabasePopulated(NamedTuple):
    database_name: str
    clinical_programme: ClinicalProgramme
    project: Project
    reason_for_lock_term_uid: str
    reason_for_unlock_term_uid: str


@pytest.fixture(scope="module")
def temp_database_populated(request, temp_database: str) -> TempDatabasePopulated:
    """temporary database with generic base data

    The data included as generic base data is the following
    - names specified below
    * Clinical Programme - ClinicalProgramme
    * Project - Project
    * Study - study_root
    * Libraries :
        * CDISC - non editable
        * Sponsor - editable
        * SNOMED - editable
    * Catalogues :
        * SDTM CT
    # Codelists
        * Those defined in CT_CODELIST_NAMES/CT_CODELIST_UIDS constants

    Returns created database name, clinical programme, project
    """

    log.info("%s: injecting base data", request.fixturename)

    ## Libraries
    TestUtils.create_library(settings.cdisc_library_name, True)
    TestUtils.create_library(SPONSOR_LIBRARY_NAME, True)
    TestUtils.create_library("SNOMED", True)
    TestUtils.create_library(name=settings.requested_library_name, is_editable=True)

    with db.write_transaction:
        cdisc = Library.nodes.get(name=settings.cdisc_library_name)

        CTCatalogue(
            name=settings.sdtm_ct_catalogue_name
        ).save().contains_catalogue.connect(cdisc)

        CTCatalogue(
            name=settings.adam_ct_catalogue_name
        ).save().contains_catalogue.connect(cdisc)

    unit_dimensions = []
    unit_dimension_codelist = TestUtils.create_ct_codelist(
        name="Unit Dimension",
        sponsor_preferred_name="unit dimension",
        extensible=True,
        approve=True,
        submission_value="UNITDIM",
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    unit_dimension_term = TestUtils.create_ct_term(
        codelist_uid=unit_dimension_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="Weight",
        sponsor_preferred_name="Weight",
    )
    unit_dimensions.append(unit_dimension_term.term_uid)

    unit_subsets = []
    unit_subset_codelist = TestUtils.create_ct_codelist(
        name="Unit Subset",
        sponsor_preferred_name="unit subset",
        extensible=True,
        approve=True,
        submission_value="UNITSUBS",
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    unit_subset_term = TestUtils.create_ct_term(
        codelist_uid=unit_subset_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="study time",
        sponsor_preferred_name="Study Time",
    )
    unit_subsets.append(unit_subset_term.term_uid)

    ## Unit Definitions
    TestUtils.create_unit_definition(
        name=settings.day_unit_name,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=settings.day_unit_conversion_factor_to_master,
        unit_subsets=unit_subsets,
    )
    TestUtils.create_unit_definition(
        name=settings.days_unit_name,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=settings.day_unit_conversion_factor_to_master,
        unit_subsets=unit_subsets,
    )
    TestUtils.create_unit_definition(
        name=settings.week_unit_name,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=settings.week_unit_conversion_factor_to_master,
        unit_subsets=unit_subsets,
    )

    ## Codelists
    TestUtils.create_ct_codelists_using_cypher()

    ## Study snapshot definition
    ## It needs CDISC Library and SDTM CT catalogue

    ## Clinical programme and project required for creating test studies
    clinical_programme = TestUtils.create_clinical_programme(
        name=TestUtils.random_str(6, "TSTCP-")
    )

    project = TestUtils.create_project(
        name=TestUtils.random_str(6, "TST Project "),
        project_number=TestUtils.random_str(6),
        description="Test project for automated tests",
        clinical_programme_uid=clinical_programme.uid,
    )
    # Create CTTerms needed for locking/unlocking
    lock_unlock_data = create_reason_for_lock_unlock_terms()
    reason_for_lock_term_uid = lock_unlock_data["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = lock_unlock_data["reason_for_unlock_terms"][0].term_uid
    return TempDatabasePopulated(
        temp_database,
        clinical_programme,
        project,
        reason_for_lock_term_uid,
        reason_for_unlock_term_uid,
    )
