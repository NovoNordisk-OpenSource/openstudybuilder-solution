import argparse

from neo4j import GraphDatabase
from os import environ
from db_schema import build_schema_queries, SCHEMA_CLEAR_QUERY
from init_utils import (
    create_special_template_parameters,
    pre_load_counter_nodes,
    pre_load_template_parameter_tree,
    provision_roles_and_users,
    run_querystring,
    run_querystring_read,
)

from datetime import datetime

parser = argparse.ArgumentParser(description="Initialize the Neo4j database")
parser.add_argument(
    "--schema",
    choices=["all", "mdr", "staging"],
    default="all",
    help="Which indexes/constraints to create: the MDR ones, the CDISC staging ones, "
    "or both (default). MDR seed data (TemplateParameter tree, :Counter nodes) is only"
    " loaded when 'all' or 'mdr' is selected.",
)
args = parser.parse_args()
SCHEMA_MDR = args.schema in ("all", "mdr")
SCHEMA_STAGING = args.schema in ("all", "staging")

DATABASE = environ.get("NEO4J_MDR_DATABASE")
DATABASE_DBNAME = environ.get("NEO4J_MDR_DATABASE_DBNAME", None)
NEO4J_MDR_CLEAR_DATABASE = environ.get("NEO4J_MDR_CLEAR_DATABASE", "false")
NEO4J_MDR_BACKUP_DATABASE = environ.get("NEO4J_MDR_BACKUP_DATABASE", "false")
CLEAR_DATABASE = NEO4J_MDR_CLEAR_DATABASE.lower() == "true"
BACKUP_DATABASE = NEO4J_MDR_BACKUP_DATABASE.lower() == "true"

uri = "neo4j://{}:{}".format(
    environ.get("NEO4J_MDR_HOST"), environ.get("NEO4J_MDR_BOLT_PORT")
)
driver = GraphDatabase.driver(
    uri,
    auth=(environ.get("NEO4J_MDR_AUTH_USER"), environ.get("NEO4J_MDR_AUTH_PASSWORD")),
)


def make_db_name():
    if (
        DATABASE_DBNAME is None
        or DATABASE_DBNAME.lower() == ""
        or DATABASE_DBNAME.lower().startswith("auto")
    ):
        now = datetime.now()
        date_str = now.strftime("%Y.%m.%d-%H.%M")
        db_name = "{}-{}".format(DATABASE, date_str)
        print(f"Using auto-generated database name: '{db_name}'")
    else:
        db_name = DATABASE_DBNAME
        print(f"Using provided database name: '{db_name}'")
    return db_name


print("\n-- Clear and backup --")
print(f"Clear database: {CLEAR_DATABASE}")
print(f"Keep backup of database: {BACKUP_DATABASE}")
# Clear database if requested
if CLEAR_DATABASE:
    with driver.session(database="system") as session:
        querystring = (
            "SHOW ALIASES FOR DATABASE YIELD * WHERE name='{}' RETURN database".format(
                DATABASE
            )
        )
        db_name_reply = session.read_transaction(run_querystring_read, querystring)
        if db_name_reply:
            db_name = db_name_reply[0]["database"]
            print(f"Dropping alias '{DATABASE}' for database '{db_name}'")
            querystring = "DROP ALIAS `{}` IF EXISTS FOR DATABASE".format(DATABASE)
            session.write_transaction(run_querystring, querystring)
            if not BACKUP_DATABASE:
                # Delete the database
                querystring = "DROP DATABASE `{}` IF EXISTS".format(db_name)
                print("Dropping database '{}'".format(db_name))
                session.write_transaction(run_querystring, querystring)
            else:
                print("Keeping database '{}'".format(db_name))
        else:
            querystring = "SHOW DATABASE `{}`".format(DATABASE)
            existing = session.read_transaction(run_querystring_read, querystring)
            if len(existing) > 0:
                print(
                    "Database '{}' already exists but is not an alias".format(DATABASE)
                )
                if BACKUP_DATABASE:
                    raise RuntimeError(
                        "Unable to keep a backup since the database is not an alias"
                    )
                else:
                    querystring = "DROP DATABASE `{}` IF EXISTS".format(DATABASE)
                    print("Dropping database '{}'".format(DATABASE))
                    session.write_transaction(run_querystring, querystring)

# Create database and alias if not exists
print("\n-- Creating database and alias --")
with driver.session(database="system") as session:
    querystring = "SHOW DATABASE `{}`".format(DATABASE)
    existing = session.read_transaction(run_querystring_read, querystring)
    if len(existing) > 0:
        print(
            "Database (or alias) '{}' already exists, skipping create step".format(
                DATABASE
            )
        )
    else:
        new_db_name = make_db_name()
        if new_db_name.lower() == DATABASE.lower():
            raise RuntimeError(
                "Database name and alias must be different. Provided db name: {new_db_name}, alias: {DATABASE}"
            )
        print("Creating database '{}'".format(new_db_name))
        querystring = "CREATE DATABASE `{}` IF NOT EXISTS".format(new_db_name)
        session.write_transaction(run_querystring, querystring)
        print("Creating alias '{}' for database '{}'".format(DATABASE, new_db_name))
        querystring = "CREATE ALIAS `{}` IF NOT EXISTS FOR DATABASE `{}`".format(
            DATABASE, new_db_name
        )
        session.write_transaction(run_querystring, querystring)

# Set up roles and permissions
print("\n-- Setting up roles and permissions --")
with driver.session(database="system") as session:
    provision_roles_and_users(session)

# Create indexes and constraints
print(f"\n-- Setting up indexes and constraints (schema: {args.schema}) --")
with driver.session(database=DATABASE) as session:
    print(SCHEMA_CLEAR_QUERY)
    session.write_transaction(run_querystring, SCHEMA_CLEAR_QUERY)

    for query in build_schema_queries(mdr=SCHEMA_MDR, staging=SCHEMA_STAGING):
        print(query)
        session.write_transaction(run_querystring, query)

    if SCHEMA_MDR:
        print(
            "\n-- Preloading TemplateParameter tree (Activity, Activity Group, Findings, Dose unit...) --"
        )
        with session.begin_transaction() as tx:
            pre_load_template_parameter_tree(tx)

        print("\n-- Creating special template parameters (NA...) --")
        with session.begin_transaction() as tx:
            create_special_template_parameters(tx)

        print("\n-- Preloading :Counter nodes --")
        with session.begin_transaction() as tx:
            pre_load_counter_nodes(tx)

    session.close()

driver.close()
