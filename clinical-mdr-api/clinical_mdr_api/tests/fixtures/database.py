# pylint: disable=unused-argument,redefined-outer-name

import logging
import time
from typing import NamedTuple
from urllib.parse import urljoin

import neo4j.exceptions
import pytest
from neomodel import config as neoconfig
from neomodel.sync_.core import db

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCatalogue,
    Library,
)
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import LIBRARY_NAME, TestUtils
from clinical_mdr_api.tests.utils.utils import get_db_name
from common import config

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
    neoconfig.DATABASE_URL = urljoin(config.settings.neo4j_dsn, "/neo4j")
    db.set_connection(neoconfig.DATABASE_URL)
    db.cypher_query("CREATE OR REPLACE DATABASE $db", {"db": db_name})

    log.debug(
        "%s fixture: altering database configuration to: %s",
        request.fixturename,
        db_name,
    )
    neoconfig.DATABASE_URL = urljoin(config.settings.neo4j_dsn, f"/{db_name}")

    try_cnt = 1
    db_available = False
    while try_cnt < 10 and not db_available:
        try:
            # Database creation can take a couple of seconds
            # db.set_connection will return a ClientError if the database isn't ready
            # This allows for retrying after a small pause
            db.set_connection(neoconfig.DATABASE_URL)

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

    config.settings = config.Settings()
    log.debug(
        "%s fixture: reset to database configuration: %s",
        request.fixturename,
        config.settings.neo4j_dsn or config.settings.neo4j_database,
    )
    neoconfig.DATABASE_URL = config.settings.neo4j_dsn
    db.set_connection(config.settings.neo4j_dsn)

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
    inject_base_data()


class TempDatabasePopulated(NamedTuple):
    database_name: str
    clinical_programme: ClinicalProgramme
    project: Project


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
    TestUtils.create_library(config.CDISC_LIBRARY_NAME, True)
    TestUtils.create_library(LIBRARY_NAME, True)
    TestUtils.create_library("SNOMED", True)
    TestUtils.create_library(name=config.REQUESTED_LIBRARY_NAME, is_editable=True)

    with db.write_transaction:
        cdisc = Library.nodes.get(name=config.CDISC_LIBRARY_NAME)

        CTCatalogue(
            name=config.SDTM_CT_CATALOGUE_NAME
        ).save().contains_catalogue.connect(cdisc)

        CTCatalogue(
            name=config.ADAM_CT_CATALOGUE_NAME
        ).save().contains_catalogue.connect(cdisc)

    unit_subsets = []
    unit_subset_codelist = TestUtils.create_ct_codelist(
        name="Unit Subset",
        sponsor_preferred_name="unit subset",
        extensible=True,
        approve=True,
    )
    unit_subset_term = TestUtils.create_ct_term(
        codelist_uid=unit_subset_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="study time",
        sponsor_preferred_name="Study Time",
    )
    unit_subsets.append(unit_subset_term.term_uid)

    ## Unit Definitions
    TestUtils.create_unit_definition(
        name=config.DAY_UNIT_NAME,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=config.DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
        unit_subsets=unit_subsets,
    )
    TestUtils.create_unit_definition(
        name=config.DAYS_UNIT_NAME,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=config.DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
        unit_subsets=unit_subsets,
    )
    TestUtils.create_unit_definition(
        name=config.WEEK_UNIT_NAME,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=config.WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
        unit_subsets=unit_subsets,
    )

    ## Codelists
    TestUtils.create_ct_codelists_using_cypher()

    ## Study snapshot definition
    ## It needs CDISC Library and SDTM CT catalogue
    TestUtils.create_study_fields_configuration()

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

    return TempDatabasePopulated(temp_database, clinical_programme, project)
