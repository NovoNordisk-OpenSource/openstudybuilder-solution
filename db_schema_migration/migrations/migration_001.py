"""Schema migrations needed for release to PROD in January 2023."""

import os
import re

from import_standards.src.scripts.utils import REPLACEMENTS

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import (
    REGEX_SNAKE_CASE_WITH_DOT,
    api_get,
    api_post,
    get_db_connection,
    get_db_result_as_dict,
    get_logger,
    snake_case,
)

logger = get_logger(os.path.basename(__file__))
DB_CONNECTION = get_db_connection()


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])
    migrate_ct_config_values(DB_CONNECTION, logger)
    migrate_study_fields(DB_CONNECTION)
    migrate_study_criteria(DB_CONNECTION)
    migrate_activities(DB_CONNECTION)
    migrate_template_parameters(DB_CONNECTION)
    migrate_term_uids(DB_CONNECTION)
    create_requested_library()
    migrate_null_flavor_list(DB_CONNECTION)
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_codelist_extensible_flag(DB_CONNECTION)


def migrate_study_fields(db_connection):
    logger.info(
        "Migrating StudyFields properties and relationships to CTTermRoot/DictionaryTermRoot"
    )

    study_fields = db_connection.cypher_query(
        "MATCH (n:StudyField) WHERE n.field_name is not null return n"
    )[0]
    for row in study_fields:
        node_properties: dict = row[0]._properties
        field_name = node_properties["field_name"]
        if not re.match(REGEX_SNAKE_CASE_WITH_DOT, field_name):
            val_snake_case = snake_case(field_name)
            logger.info(
                "Converting StudyField {field_name: '%s'} to '%s' and creating missing type relationships to CTTermRoot/DictionaryTermRoot",
                field_name,
                val_snake_case,
            )
            statement = f"""
                        MATCH (study_field:StudyField)
                        WHERE ID(study_field) = {row[0].id}
                        SET study_field.field_name = '{val_snake_case}'
                        WITH study_field
                        MATCH (config_value:CTConfigValue {{study_field_name: '{val_snake_case}'}})
                        WITH study_field, config_value,
                        CASE 
                        WHEN study_field:StudyBooleanField AND study_field.value=true THEN "C49488_Y"
                        WHEN study_field:StudyBooleanField AND study_field.value=false THEN "C49487_N"
                        ELSE study_field.value
                        END AS node_uid
                        WITH study_field, node_uid
                        UNWIND node_uid as n_uid
                        MATCH (new_type_node {{uid:n_uid}})
                        CALL apoc.do.case([
                            // new type node is of CTTerm type 
                            new_type_node:CTTermRoot,
                            'MERGE (study_field)-[:HAS_TYPE]->(new_type_node)',
                        
                            // new type node is of DictionaryTerm type
                            new_type_node:DictionaryTermRoot,
                            'MERGE (study_field)-[:HAS_DICTIONARY_TYPE]->(new_type_node)'
                        ], 
                        '',
                        {{
                            study_field: study_field, 
                            new_type_node: new_type_node
                        }})
                        YIELD value
                        RETURN value
                        """
            db_connection.cypher_query(statement)


# pylint: disable=unused-argument
def migrate_activities(db_connection):
    # Remove unnecessary IN_SUB_GROUP/IN_GROUP outgoing relations from ActivityValue/ActivitySubGroupValue nodes:
    # - (n:ActivityValue)-[r:IN_SUB_GROUP]->(m:ActivitySubGroupValue)
    # - (n:ActivitySubGroupValue)-[r:IN_GROUP]->(m:ActivityGroupValue)
    #
    # Multiple outgoing relations of these types are no longer allowed.
    # After migration, only one of these outgoing relations will be left on each node.

    logger.info("Migrating activities...")
    query_activities = """
        MATCH (n:ActivityValue)-[r:IN_SUB_GROUP]->(m:ActivitySubGroupValue)
        WITH n, count(m) as nbr_rels, collect(m)[1..] as ms, collect(r)[1..] as rels
        WHERE nbr_rels > 1
        """
    query_groups = """
        MATCH (n:ActivitySubGroupValue)-[r:IN_GROUP]->(m:ActivityGroupValue)
        WITH n, count(m) as nbr_rels, collect(m)[1..] as ms, collect(r)[1..] as rels
        WHERE nbr_rels > 1
        """
    return_items = """
        RETURN n, id(n) as n_id, [t in ms | id(t)] as m_ids, [rel in rels | [id(startNode(rel)), id(endNode(rel))]] as r_ids, ms, rels
        """
    delete_items = "FOREACH (r in rels | DELETE r)"

    # Identify and log the affected nodes/relationships
    rows, columns = db_connection.cypher_query(query_activities + return_items)
    for row in rows:
        item = get_db_result_as_dict(row, columns)
        subgroups = [f"'{m['name']}'" for m in item["ms"]]
        log_line = f"Activity '{item['n']['name']}' is in multiple subgroups, will remove from {', '.join(subgroups)}"
        logger.info(log_line)

    rows, columns = db_connection.cypher_query(query_groups + return_items)
    for row in rows:
        item = get_db_result_as_dict(row, columns)
        groups = [f"'{m['name']}'" for m in item["ms"]]
        log_line = f"Activity subgroup '{item['n']['name']}' is in multiple groups, will remove from {', '.join(groups)}"
        logger.info(log_line)

    # Remove unnecessary IN_SUB_GROUP and IN_GROUP relations
    db_connection.cypher_query(query_activities + delete_items)
    db_connection.cypher_query(query_groups + delete_items)


def migrate_template_parameters(db_connection):
    # Add `TemplateParameter {name: "StudyEndpoint"}` node if it doesn't already exist
    logger.info("Migrating template parameters...")
    logger.info(
        'Adding node if it doesn\'t exist: TemplateParameter {name: "StudyEndpoint"}'
    )
    db_connection.cypher_query(
        'MERGE (endpoint:TemplateParameter {name: "StudyEndpoint"})'
    )


def migrate_study_criteria(db_connection):
    # Add `key_criteria` boolean property to `StudyCriteria` nodes
    logger.info("Migrating study criteria...")
    result = db_connection.cypher_query("MATCH (n:StudyCriteria) return n")
    for row in result[0]:
        node_properties: dict = row[0]._properties
        if "key_criteria" not in node_properties:
            logger.info(
                "Setting key_criteria property on StudyCriteria {uid: %s} node",
                node_properties["uid"],
            )
            statement = f"""
                MATCH (n:StudyCriteria)
                WHERE ID(n) = {row[0].id}
                SET n.key_criteria = false                    
                """
            db_connection.cypher_query(statement)


def migrate_term_uids(db_connection):
    logger.info("Migrating CT term uids...")
    replace_chars = "\n".join(
        [
            f'WITH replace(submval, "{old}", "{new}") AS submval'
            for old, new in REPLACEMENTS
        ]
    )

    query_start = """
        MATCH (n:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(m:CTTermAttributesRoot)-[:LATEST]-(o:CTTermAttributesValue)
        WHERE (n)<-[:CONTAINS_TERM]-(:Library {name: "CDISC"})
        CALL { WITH o
            WITH o.code_submission_value AS submval
    """

    query_end = """
            RETURN submval
        }
        SET n.uid = n.concept_id + "_" + submval
    """

    db_connection.cypher_query(query_start + replace_chars + query_end)


def create_requested_library():
    existing = api_get("/libraries").json()
    if any(lib["name"] == "Requested" for lib in existing):
        logger.info("'Requested' library already exists, no need to create")
        return
    data = {"name": "Requested", "is_editable": True}
    logger.info("Creating 'Requested' library")
    api_post(path="/libraries", payload=data)


def migrate_null_flavor_list(db_connection):
    logger.info("Migrating null flavor codelist terms...")
    logger.info("Replace NOT APPLICABLE with NA")
    db_connection.cypher_query("""
        MATCH (n:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]-({code_submission_value: "NOT APPLICABLE"}),
        (n)<-[has_term:HAS_TERM]-(l:CTCodelistRoot)-[:HAS_NAME_ROOT]-(nr:CTCodelistNameRoot)-[:LATEST]-(name {name: "Null Flavor"}),
        (n)<-[reason:HAS_REASON_FOR_NULL_VALUE]-(f)
        MATCH (na:CTTermRoot {uid: "C48660_NA"})
        CALL apoc.refactor.to(has_term, na)
        YIELD input AS i1, output AS o1
        CALL apoc.refactor.to(reason, na)
        YIELD input AS i2, output AS o2
        RETURN *
    """)
    logger.info("Remove QS from list")
    db_connection.cypher_query("""
        MATCH (n:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-()-[:LATEST]-({code_submission_value: "QS"}),
        (n)-[r:HAS_TERM]-(l:CTCodelistRoot)-[:HAS_NAME_ROOT]-(nr:CTCodelistNameRoot)-[:LATEST]-(name {name: "Null Flavor"})
        DELETE r
    """)


def migrate_codelist_extensible_flag(db_connection):
    logger.info("Making all Sponsor codelists extensible")
    db_connection.cypher_query("""
        MATCH (clr:CTCodelistRoot)-[har:HAS_ATTRIBUTES_ROOT]-(ar)-[]-(av {extensible: false}), (clr)-[:CONTAINS_CODELIST]-(lib {name: "Sponsor"})
        SET av.extensible = true
        """)


if __name__ == "__main__":
    main()
