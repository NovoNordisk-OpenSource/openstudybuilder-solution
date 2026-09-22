import csv

from db.db_schema import build_schema_queries

from migrations.utils.utils import api_post, drop_indexes_and_constraints

REGEX_SNAKE_CASE = r"^[a-z]+(_[a-z]+)*$"
REGEX_SNAKE_CASE_WITH_DOT = r"^[a-z.]+(_[a-z.]+)*$"


def migrate_indexes_and_constraints(db_connection, logger):
    logger.info("Re-creating all db indexes and constraints...")

    drop_indexes_and_constraints()

    for query in build_schema_queries():
        logger.info(query)
        db_connection.cypher_query(query)


def migrate_ct_config_values(db_connection, logger):
    logger.info("Re-creating CTConfig values...")
    # Remove all CTConfigRoot/Value nodes and recreate them by issuing POST /configurations requests,
    # based on study fields configuration csv file.
    db_connection.cypher_query(
        "MATCH (val:CTConfigValue)-[r]-(root:CTConfigRoot) DETACH DELETE root, val"
    )
    db_connection.cypher_query(
        "MATCH (val:CTConfigValue)-[r]-(root:DeletedCTConfigRoot) DETACH DELETE root, val"
    )

    filename = (
        "../import_sponsor_data/datafiles/configuration/study_fields_configuration.csv"
    )
    with open(filename, encoding="utf-8", errors="ignore") as csv_file:
        for line in csv.DictReader(csv_file):
            # Replace empty strings with None
            line = {k: v if v != "" else None for k, v in line.items()}
            # DictReader yields strings; /configurations expects a JSON boolean.
            if "is_dictionary_term" in line:
                line["is_dictionary_term"] = (
                    str(line.get("is_dictionary_term")).strip().lower() == "true"
                )
            logger.info(
                "Adding CTConfigRoot/Value for study field '%s'",
                line["study_field_name"],
            )
            api_post(path="/configurations", payload=line)
