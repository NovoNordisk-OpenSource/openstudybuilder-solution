"""Schema migrations needed for release 1.8 to PROD post August 2024."""

import os

from import_sponsor_data.importers.run_import_compounds import (
    Compounds as CompoundsImporter,
)
from import_sponsor_data.importers.utils.metrics import Metrics

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import (
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
NON_VISIT_NUMBER = 29999
UNSCHEDULED_VISIT_NUMBER = 29500
MIGRATION_DESC = "schema-migration-release-1.8"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_non_visit_and_unscheduled_visit_number_reversal(DB_DRIVER, logger)
    remove_existing_library_compounds(DB_DRIVER, logger)
    remove_existing_study_compounds(DB_DRIVER, logger)
    import_library_compounds(logger)


def remove_existing_library_compounds(db_driver, log):
    db_changes = []

    log.info("Removing existing library compounds")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (cr:CompoundRoot)-[]-(cv:CompoundValue)
        DETACH DELETE cr, cv
        """,
    )
    print_counters_table(summary.counters)
    db_changes.append(summary.counters.contains_updates)

    logger.info("Removing existing library compound aliases")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (car:CompoundAliasRoot)-[]-(cav:CompoundAliasValue)
        DETACH DELETE car, cav
        """,
    )
    print_counters_table(summary.counters)
    db_changes.append(summary.counters.contains_updates)

    logger.info("Removing existing library medicinal products")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (mpr:MedicinalProductRoot)-[]-(mpv:MedicinalProductValue)
        DETACH DELETE mpr, mpv
        """,
    )
    print_counters_table(summary.counters)
    db_changes.append(summary.counters.contains_updates)

    logger.info("Removing existing library active substances")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (asr:ActiveSubstanceRoot)-[]-(asv:ActiveSubstanceValue)
        DETACH DELETE asr, asv
        """,
    )
    print_counters_table(summary.counters)
    db_changes.append(summary.counters.contains_updates)

    logger.info("Removing existing library pharmaceutical products")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (ppr:PharmaceuticalProductRoot)-[]-(ppv:PharmaceuticalProductValue)
        DETACH DELETE ppr, ppv
        """,
    )
    print_counters_table(summary.counters)
    db_changes.append(summary.counters.contains_updates)

    return db_changes


def remove_existing_study_compounds(db_driver, log):
    db_changes = []

    log.info("Removing existing study compounds")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (sc:StudyCompound)
        DETACH DELETE sc
        """,
    )

    print_counters_table(summary.counters)
    db_changes.append(summary.counters.contains_updates)

    logger.info("Removing existing study compound dosings")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (scd:StudyCompoundDosing)
        DETACH DELETE scd
        """,
    )

    print_counters_table(summary.counters)
    db_changes.append(summary.counters.contains_updates)

    return db_changes


def import_library_compounds(log):
    log.info("Importing library compounds from json files")
    compounds_importer = CompoundsImporter(metrics_inst=Metrics())
    compounds_importer.run()


def migrate_non_visit_and_unscheduled_visit_number_reversal(db_driver, log):
    log.info("Reversing numbers for non-visit and unscheduled-visit")
    _, non_visit_summary = run_cypher_query(
        db_driver,
        """
        MATCH (non_visit:StudyVisit)-[old_visit_name:HAS_VISIT_NAME]->(visit_name_root:SimpleConceptRoot)
        WHERE non_visit.visit_class='NON_VISIT' AND non_visit.visit_number <> $non_visit_number
        SET non_visit.visit_number = $non_visit_number
        SET non_visit.unique_visit_number = $non_visit_number
        SET non_visit.short_visit_label = $non_visit_number
        WITH non_visit, old_visit_name
        MATCH (new_visit_name_root:SimpleConceptRoot)-[:LATEST]->(:SimpleConceptValue {name:$visit_name})
        MERGE (non_visit)-[:HAS_VISIT_NAME]->(new_visit_name_root)
        DETACH DELETE old_visit_name
        RETURN *
        """,
        params={
            "non_visit_number": NON_VISIT_NUMBER,
            "visit_name": f"Visit {NON_VISIT_NUMBER}",
        },
    )
    non_visit_counters = non_visit_summary.counters
    print_counters_table(non_visit_counters)

    _, unscheduled_visit_summary = run_cypher_query(
        db_driver,
        """
        MATCH (unscheduled_visit:StudyVisit)-[old_visit_name:HAS_VISIT_NAME]->(visit_name_root:SimpleConceptRoot)
        WHERE unscheduled_visit.visit_class='UNSCHEDULED_VISIT' AND unscheduled_visit.visit_number <> $unscheduled_visit_number
        SET unscheduled_visit.visit_number = $unscheduled_visit_number
        SET unscheduled_visit.unique_visit_number = $unscheduled_visit_number
        SET unscheduled_visit.short_visit_label = $unscheduled_visit_number
        WITH unscheduled_visit, old_visit_name
        MATCH (new_visit_name_root:SimpleConceptRoot)-[:LATEST]->(:SimpleConceptValue {name:$visit_name})
        MERGE (unscheduled_visit)-[:HAS_VISIT_NAME]->(new_visit_name_root)
        DETACH DELETE old_visit_name
        RETURN *
        """,
        params={
            "unscheduled_visit_number": UNSCHEDULED_VISIT_NUMBER,
            "visit_name": f"Visit {UNSCHEDULED_VISIT_NUMBER}",
        },
    )
    unscheduled_visit_counters = unscheduled_visit_summary.counters
    print_counters_table(unscheduled_visit_counters)

    return (
        non_visit_counters.contains_updates
        or unscheduled_visit_counters.contains_updates
    )


if __name__ == "__main__":
    main()
