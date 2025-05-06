""" PRD Data Corrections, for release 1.11.2"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_010

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.11.2"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    remove_user_initials_field_from_all_nodes(DB_DRIVER, LOGGER, run_label)
    remove_user_initials_field_from_all_relations(DB_DRIVER, LOGGER, run_label)
    remove_relationship_between_intervention_and_activity_instance_template_parameters(
        DB_DRIVER, LOGGER, run_label
    )
    create_qphm_user(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_010.test_remove_user_initials_field_from_all_nodes
)
def remove_user_initials_field_from_all_nodes(db_driver, log, run_label):
    """
    Remove the `user_initials` field from all nodes
    """
    desc = "Removing the `user_initials` field from all nodes"
    log.info(f"Run: {run_label}, {desc}")

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (n)
        WHERE n.author_id is not null
        REMOVE n.user_initials
        """,
    )

    return summary_nodes.counters.contains_updates


@capture_changes(
    verify_func=correction_verification_010.test_remove_user_initials_field_from_all_relations
)
def remove_user_initials_field_from_all_relations(db_driver, log, run_label):
    """
    Remove the `user_initials` field from all relationships
    """
    desc = "Removing the `user_initials` field from all relationships"
    log.info(f"Run: {run_label}, {desc}")

    _, summary_rels = run_cypher_query(
        db_driver,
        """
        MATCH ()-[rel]->()
        WHERE rel.author_id is not null
        REMOVE rel.user_initials
        """,
    )

    return summary_rels.counters.contains_updates


@capture_changes(verify_func=correction_verification_010.test_create_qphm_user)
def create_qphm_user(db_driver, log, run_label):
    """
    Create User node for QPHM user that doesn't exist in MS Graph anymore,
    and update author_id field on all relevant nodes and relationships to use this user's id
    """

    oid = "5f92937a-09ad-498b-8b43-7f5060753e34"
    email = "qphm@novonordisk.com"
    name = "(QPHM) Jesper Ejlebæk Holm"

    log.info(f"Run: {run_label}, Creating User node for QPHM user")
    _, summary_rels = run_cypher_query(
        db_driver,
        """
        MERGE (u:User {user_id: $id})
        ON CREATE
            SET u.created = datetime(),
                u.oid = $oid,
                u.username = $username,
                u.name = $name,
                u.email = $email
        ON MATCH
            SET u.updated = datetime(),
                u.oid = $oid,
                u.username = $username,
                u.name = $name,
                u.email = $email
        """,
        params={
            "id": oid,
            "oid": oid,
            "username": email,
            "name": name,
            "email": email,
        },
    )

    log.info(
        f"Run: {run_label}, Updating author_id from 'qphm' to '{oid}' in all relevant nodes"
    )
    _, summary_rels = run_cypher_query(
        db_driver,
        """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.author_id = 'qphm'
        WITH n
        SET n.author_id = $oid
        """,
        params={
            "oid": oid,
        },
    )

    log.info(
        f"Run: {run_label}, Updating author_id from 'qphm' to '{oid}' in all relevant relationships"
    )
    _, summary_rels = run_cypher_query(
        db_driver,
        """
        MATCH (n)-[ver:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_DRAFT|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE ver.author_id = 'qphm'
        WITH ver
        SET ver.author_id = $oid
        """,
        params={
            "oid": oid,
        },
    )

    return summary_rels.counters.contains_updates


@capture_changes(
    verify_func=correction_verification_010.test_remove_relationship_between_intervention_and_activity_instance_template_parameters
)
def remove_relationship_between_intervention_and_activity_instance_template_parameters(
    db_driver, log, run_label
):
    """
    Remove the `:HAS_PARENT_PARAMETER` relationship between Intervention and Activity Instance `:TemplateParameter` nodes
    """
    desc = "Remove the `:HAS_PARENT_PARAMETER` relationship between Intervention and Activity Instance `:TemplateParameter` nodes"
    log.info(f"Run: {run_label}, {desc}")

    _, summary_rels = run_cypher_query(
        db_driver,
        """
        MATCH (:TemplateParameter {name:"Intervention"})-[rel]->(:TemplateParameter {name:"ActivityInstance"})
        DETACH DELETE rel
        """,
    )

    return summary_rels.counters.contains_updates


if __name__ == "__main__":
    main()
