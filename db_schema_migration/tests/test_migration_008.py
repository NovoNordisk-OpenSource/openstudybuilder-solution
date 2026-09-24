import json
import os

import pytest

from migrations import migration_008
from migrations.utils.utils import (
    api_get_paged,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_008 import TEST_DATA
from tests.utils.utils import clear_db

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=broad-except

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

db = get_db_connection()
DB_DRIVER = get_db_driver()
logger = get_logger(os.path.basename(__file__))


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_008.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_non_visit_and_unscheduled_visit_number_reversal(migration):
    logger.info("Check for visit numbers of non visit and unscheduled visit")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_visit:StudyVisit)-[:HAS_VISIT_NAME]->(visit_name_root:SimpleConceptRoot)
        WITH study_visit, collect(visit_name_root) as visit_names
        WHERE size(visit_names) > 1
        RETURN *
        """,
        params={
            "non_visit_number": migration_008.NON_VISIT_NUMBER,
            "visit_name": f"Visit {migration_008.NON_VISIT_NUMBER}",
        },
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} Found some StudyVisit with multiple visit names"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (non_visit:StudyVisit)-[:HAS_VISIT_NAME]->(:SimpleConceptRoot)-[:LATEST]->(visit_name_value:SimpleConceptRoot)
        WHERE non_visit.visit_class='NON_VISIT' AND (non_visit.visit_number <> $non_visit_number OR visit_name_value.name <> $visit_name)
        RETURN *
        """,
        params={
            "non_visit_number": migration_008.NON_VISIT_NUMBER,
            "visit_name": f"Visit {migration_008.NON_VISIT_NUMBER}",
        },
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} Non visit having wrong visit number or visit name"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (unscheduled_visit:StudyVisit)-[:HAS_VISIT_NAME]->(:SimpleConceptRoot)-[:LATEST]->(visit_name_value:SimpleConceptRoot)
        WHERE unscheduled_visit.visit_class='UNSCHEDULED_VISIT' AND (unscheduled_visit.visit_number <> $unscheduled_visit_number OR visit_name_value.name <> $visit_name)
        RETURN *
        """,
        params={
            "unscheduled_visit_number": migration_008.UNSCHEDULED_VISIT_NUMBER,
            "visit_name": f"Visit {migration_008.UNSCHEDULED_VISIT_NUMBER}",
        },
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} Unscheduled visit having wrong visit number or visit name"

    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying that non and unscheduled visits have proper numbers in the following Study (%s)",
            study_uid,
        )
        study_visits = api_get_paged(f"/studies/{study_uid}/study-visits", page_size=10)
        for study_visit in study_visits["items"]:
            if study_visit["visit_class"] == "UNSCHEDULED_VISIT":
                assert (
                    int(study_visit["visit_number"])
                    == migration_008.UNSCHEDULED_VISIT_NUMBER
                )
                assert (
                    int(study_visit["unique_visit_number"])
                    == migration_008.UNSCHEDULED_VISIT_NUMBER
                )
                assert (
                    int(study_visit["visit_short_name"])
                    == migration_008.UNSCHEDULED_VISIT_NUMBER
                )
                assert (
                    study_visit["visit_name"]
                    == f"Visit {migration_008.UNSCHEDULED_VISIT_NUMBER}"
                )
            elif study_visit["visit_class"] == "NON_VISIT":
                assert (
                    int(study_visit["visit_number"]) == migration_008.NON_VISIT_NUMBER
                )
                assert (
                    int(study_visit["unique_visit_number"])
                    == migration_008.NON_VISIT_NUMBER
                )
                assert (
                    int(study_visit["visit_short_name"])
                    == migration_008.NON_VISIT_NUMBER
                )
                assert (
                    study_visit["visit_name"]
                    == f"Visit {migration_008.NON_VISIT_NUMBER}"
                )


@pytest.mark.order(after="test_migrate_non_visit_and_unscheduled_visit_number_reversal")
def test_repeat_migrate_non_visit_and_unscheduled_visit_number_reversal(migration):
    assert not migration_008.migrate_non_visit_and_unscheduled_visit_number_reversal(
        DB_DRIVER, logger
    )


def test_library_compounds(migration, verify_number_of_entities: bool = False):
    res_compounds = api_get_paged("/concepts/compounds")
    res_as = api_get_paged("/concepts/active-substances")
    res_pp = api_get_paged("/concepts/pharmaceutical-products")
    res_mp = api_get_paged("/concepts/medicinal-products")

    if verify_number_of_entities:
        with open(os.getenv("MDR_MIGRATION_COMPOUNDS"), encoding="utf-8") as file:
            compounds = json.load(file)
            assert len(res_compounds["items"]) == len(
                compounds
            ), "Number of created compounds is not equal to the number of compounds in the json file"

        with open(
            os.getenv("MDR_MIGRATION_PHARMACEUTICAL_PRODUCTS"), encoding="utf-8"
        ) as file:
            pharmaceutical_products = json.load(file)
            assert len(res_pp["items"]) == len(
                pharmaceutical_products
            ), "Number of created pharmaceutical products is not equal to the number of pharmaceutical products in the json file"

        with open(
            os.getenv("MDR_MIGRATION_ACTIVE_SUBSTANCES"), encoding="utf-8"
        ) as file:
            active_substances = json.load(file)
            assert len(res_as["items"]) == len(
                active_substances
            ), "Number of created active substances is not equal to the number of active substances in the json file"

        with open(
            os.getenv("MDR_MIGRATION_MEDICINAL_PRODUCTS"), encoding="utf-8"
        ) as file:
            medicinal_products = json.load(file)
            assert len(res_mp["items"]) == len(
                medicinal_products
            ), "Number of created medicinal products is not equal to the number of medicinal products in the json file"


def test_study_compounds(migration):
    query = """
        MATCH (sc:StudyCompound) 
        RETURN sc
    """
    result = run_cypher_query(DB_DRIVER, query)
    assert (
        len(result[0]) == 0
    ), "There shouldn't be any StudyCompound nodes in the database"

    query = """
        MATCH (scd:StudyCompoundDosing)
        RETURN scd
    """
    result = run_cypher_query(DB_DRIVER, query)
    assert (
        len(result[0]) == 0
    ), "There shouldn't be any StudyCompoundDosing nodes in the database"
