from neo4j import GraphDatabase
from os import environ
from db_schema import build_schema_queries, drop_indexes_and_constraints
from init_utils import (
    create_special_template_parameters,
    pre_load_counter_nodes,
    pre_load_template_parameter_tree,
    provision_roles_and_users,
)

DATABASE = environ.get("NEO4J_MDR_DATABASE")
NEO4J_MDR_CLEAR_DATABASE = environ.get("NEO4J_MDR_CLEAR_DATABASE", "false")
CLEAR_DATABASE = NEO4J_MDR_CLEAR_DATABASE.lower() == "true"

uri = "neo4j+s://{}".format(environ.get("NEO4J_MDR_HOST"))
driver = GraphDatabase.driver(
    uri,
    auth=(environ.get("NEO4J_MDR_AUTH_USER"), environ.get("NEO4J_MDR_AUTH_PASSWORD")),
)


print("\n-- Clear and backup --")
print(f"Clear database: {CLEAR_DATABASE}")
# Clear database if requested
if CLEAR_DATABASE:
    with driver.session(database=DATABASE) as session:
        querystring = (
            "MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS"
        )
        session.run(querystring)

# Set up roles and permissions
print("\n-- Setting up roles and permissions --")
with driver.session(database="system") as session:
    provision_roles_and_users(session)

# Create indexes and constraints
print("\n-- Setting up indexes and constraints on specific nodes --")
with driver.session(database=DATABASE) as session:
    drop_indexes_and_constraints(session)

    for query in build_schema_queries():
        print(query)
        session.run(query)

    print(
        "\n-- Preloading TemplateParameter tree (Activity, Activity Group, Findings, Dose unit...) --"
    )
    with session.begin_transaction() as tx:
        pre_load_template_parameter_tree(tx)

    print("\n-- Creating special template parameters (NA...) --")
    with session.begin_transaction() as tx:
        create_special_template_parameters(tx)

    print(
        "\n-- Preloading :Counter nodes --"
    )
    with session.begin_transaction() as tx:
        pre_load_counter_nodes(tx)

    session.close()

driver.close()
