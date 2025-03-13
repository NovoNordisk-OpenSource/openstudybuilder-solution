""" Schema migrations needed for release 1.11.0 to PROD post December 2024."""

import asyncio
import os

from clinical_mdr_api.clinical_mdr_api.models.integrations.msgraph import GraphUser
from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils import msgraph
from migrations.utils.utils import (
    api_get,
    api_post,
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-1.11.0"
SB_APP_REGISTRATION_ID = "fd909732-bc9e-492b-a1ed-6e27757a4f00"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_unit_definition_properties(DB_DRIVER, logger)
    migrate_preferred_time_unit(DB_DRIVER, logger)
    migrate_soa_preferred_time_unit(DB_DRIVER, logger)
    save_protocol_soa_snapshot_for_locked_study_versions()
    migrate_unify_study_visit_window_units(DB_DRIVER, logger)
    migrate_study_selection_metadata_merge(DB_DRIVER, logger)
    migrate_user_initials_into_author_id_and_user_nodes(DB_DRIVER, logger)


def migrate_unit_definition_properties(db_driver, log) -> list:
    contains_updates = []

    log.info(
        "Updating values of `UnitDefinitionValue.molecular_weight_conv_expon` from `null` to `false, `0` to `false` and `1` to `true`"
    )
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (u:UnitDefinitionValue)
        SET u.molecular_weight_conv_expon = 
        CASE 
            WHEN u.molecular_weight_conv_expon IS NULL AND u.use_molecular_weight IS NULL THEN false
            WHEN u.molecular_weight_conv_expon = 0 THEN false
            WHEN u.molecular_weight_conv_expon = 1 THEN true
            ELSE u.molecular_weight_conv_expon
        END
        """,
    )
    print_counters_table(summary.counters)
    contains_updates.append(summary.counters.contains_updates)

    log.info("Renaming `molecular_weight_conv_expon` to `use_molecular_weight`")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.molecular_weight_conv_expon IS NOT NULL
        SET u.use_molecular_weight = u.molecular_weight_conv_expon
        REMOVE u.molecular_weight_conv_expon
        """,
    )
    print_counters_table(summary.counters)
    contains_updates.append(summary.counters.contains_updates)

    log.info(
        "Adding new `use_complex_unit_conversion` property to `UnitDefinitionValue`"
    )
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.use_complex_unit_conversion IS NULL
        SET u.use_complex_unit_conversion = false
        """,
    )
    print_counters_table(summary.counters)
    contains_updates.append(summary.counters.contains_updates)

    return contains_updates


def migrate_user_initials_into_author_id_and_user_nodes(db_driver, log) -> bool:
    log.info(
        "Refactoring user identification: Using `author_id` field and `User` nodes instead of `user_initials` field"
    )

    _correct_had_term_relations(db_driver, log)

    # Steps:
    #   1. Copy values of `user_initials` to `author_id`
    #   2. Query AD for all unique users based on their initials (create `user_initials -> user_id` mapping)
    #   3. Create `User` nodes for all unique users using info retrieved from AD
    #   4. Update all `author_id` fields with corresponding `user_id` values (using `user_initials -> user_id` mapping from step 2.)

    updates_copy_user_initials = _copy_user_initials_to_author_id(db_driver, log)
    user_infos = _query_ad_users_based_on_user_initials(db_driver, log)
    updates_create_user_nodes = _create_user_nodes_based_on_ad_user_info(
        db_driver, log, user_infos
    )
    updates_author_id = _update_author_id_based_on_ad_user_info(
        db_driver, log, user_infos
    )
    log.info(
        "Migration completed: %s, %s, %s",
        updates_copy_user_initials,
        updates_create_user_nodes,
        updates_author_id,
    )
    return updates_copy_user_initials or updates_create_user_nodes or updates_author_id


def _correct_had_term_relations(db_driver, log) -> bool:
    # Two HAD_TERM relations in PRD are missing user_initials
    log.info("Correcting HAD_TERM relations that miss user_initials")

    # Set HAD_TERM.user_initials field value for all HAD_TERM relations that miss them
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH ()-[rel:HAD_TERM]->()
        WHERE rel.user_initials is null
        SET rel.user_initials = $sb_app_registration_id
        """,
        params={"sb_app_registration_id": SB_APP_REGISTRATION_ID},
    )

    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def _copy_user_initials_to_author_id(db_driver, log) -> bool:
    log.info("Copy values of `user_initials` to `author_id` in all nodes/relations.")

    _, node_fields_summary = run_cypher_query(
        db_driver,
        """
        // Copy node property
        CALL apoc.periodic.iterate(
            "MATCH (n:CTPackage|StudyAction|Edit|Create|Delete) WHERE n.user_initials is not null RETURN n",
            "SET n.author_id = n.user_initials",
            {batchSize: 1000}
        )
        YIELD batch, operations;
        """,
    )

    node_fields_counters = node_fields_summary.counters
    print_counters_table(node_fields_counters)

    _, relationship_fields_summary = run_cypher_query(
        db_driver,
        """
        // Copy relationship property
        CALL apoc.periodic.iterate(
            "MATCH ()-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_DRAFT|LATEST_LOCKED|LATEST_RELEASED]-() WHERE rel.user_initials is not null RETURN rel",
            "SET rel.author_id = rel.user_initials",
            {batchSize: 1000}
        )
        YIELD batch, operations;
        """,
    )

    relationship_counters = relationship_fields_summary.counters
    print_counters_table(relationship_counters)

    return (
        node_fields_counters.contains_updates or relationship_counters.contains_updates
    )


def _query_ad_users_based_on_user_initials(db_driver, log) -> dict:
    log.info("Find all unique users in DB")

    # All of these user_initials should be merged into one user
    sb_import_user_initials = [
        "test".lower(),
        "TESTUSER".lower(),
        "TODO Initials".lower(),
        "TODO user initials".lower(),
        "unknown-user".lower(),
        SB_APP_REGISTRATION_ID.lower(),
        "Import-procedure".lower(),
        "sb-import".lower(),
        None,
    ]

    unique_user_initials_from_nodes, _ = run_cypher_query(
        db_driver,
        """
            MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
            WITH COLLECT(DISTINCT (toLower(n.user_initials))) as initials,
                 COLLECT(DISTINCT (toLower(n.author_id))) as author_ids
            UNWIND (author_ids + initials) AS initials_to_migrate
            RETURN initials_to_migrate
            """,
    )

    unique_user_initials_from_nodes = list(
        map(lambda x: x["initials_to_migrate"], unique_user_initials_from_nodes)
    )

    log.info(
        "Found %s unique user_initials in nodes: %s",
        len(unique_user_initials_from_nodes),
        unique_user_initials_from_nodes,
    )

    unique_user_initials_from_relations, _ = run_cypher_query(
        db_driver,
        """
            MATCH (n)-[ver:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_DRAFT|LATEST_LOCKED|LATEST_RELEASED]->(m)
            WITH COLLECT(DISTINCT toLower(ver.author_id)) as author_ids,
                 COLLECT(DISTINCT toLower(ver.user_initials)) as initials
            UNWIND (author_ids + initials) AS initials_to_migrate
            RETURN initials_to_migrate
            """,
    )

    unique_user_initials_from_relations = list(
        map(lambda x: x["initials_to_migrate"], unique_user_initials_from_relations)
    )

    log.info(
        "Found %s unique user_initials in relations: %s",
        len(unique_user_initials_from_relations),
        unique_user_initials_from_relations,
    )

    unique_user_initials = []

    for x in unique_user_initials_from_nodes:
        if x not in unique_user_initials and x not in sb_import_user_initials:
            unique_user_initials.append(x)

    for x in unique_user_initials_from_relations:
        if x not in unique_user_initials and x not in sb_import_user_initials:
            unique_user_initials.append(x)

    log.info(
        "All unique user initials to lookup in AD (%s): %s",
        len(unique_user_initials),
        unique_user_initials,
    )

    # Create `user_intials` -> `user_info` mapping
    user_infos = {}

    # We don't want to query AD for user_initials originating from our import procedures
    for x in sb_import_user_initials:
        user_infos[x] = {
            "id": SB_APP_REGISTRATION_ID,
            "username": "sb-import",
        }

    log.info("Query AD for all unique users based on their initials")
    for x in unique_user_initials:
        user_info_from_ad = asyncio.run(_get_user_from_ad(x))
        user_infos[x] = user_info_from_ad

    log.info("All user infos: %s", user_infos)
    return user_infos


def _create_user_nodes_based_on_ad_user_info(db_driver, log, user_infos: dict) -> bool:
    log.info("Create `User` nodes for all unique users using info retrieved from AD")

    updates = False

    for user_initials, user_info in user_infos.items():
        log.info("Initials '%s' => User Info %s", user_initials, user_info)
        log.info(
            "Create `User` node: {user_id: %s, username: %s}",
            user_info.get("id", user_initials),
            user_info.get("username", user_initials),
        )

        _, user_nodes_summary = run_cypher_query(
            db_driver,
            """
            MERGE (u:User {user_id: $id})
            ON CREATE
                SET u.created = datetime(),
                    u.oid = $oid,
                    u.azp = $azp,
                    u.username = $username,
                    u.name = $name,
                    u.email = $email
            ON MATCH
                SET u.updated = datetime(),
                    u.oid = $oid,
                    u.azp = $azp,
                    u.username = $username,
                    u.name = $name,
                    u.email = $email
            """,
            params={
                "id": user_info.get("id", user_initials),
                "username": user_info.get("username", user_initials),
                "oid": user_info.get("oid", user_initials),
                "azp": user_info.get("azp", user_initials),
                "name": user_info.get("name", user_initials),
                "email": user_info.get("email", user_initials),
            },
        )

        print_counters_table(user_nodes_summary.counters)

        updates = updates or user_nodes_summary.counters.nodes_created > 0

    return updates


def _update_author_id_based_on_ad_user_info(db_driver, log, user_infos: dict) -> bool:
    log.info("Update all `author_id` fields with corresponding `user_id` values")

    updates = False

    for user_initials, user_info in user_infos.items():
        log.info(
            "Set all 'author_id' fields with value '%s' to '%s'",
            user_initials,
            user_info.get("id", user_initials),
        )

        if user_initials:
            # Set author_id on nodes
            _, nodes_summary = run_cypher_query(
                db_driver,
                """
                MATCH (n) 
                WHERE toLower(n.author_id) = $user_initials
                SET n.author_id = $user_id
                """,
                params={
                    "user_initials": user_initials.lower(),
                    "user_id": user_info.get("id", user_initials),
                },
            )
            print_counters_table(nodes_summary.counters)

            # Set author_id on relations
            _, rels_summary = run_cypher_query(
                db_driver,
                """
                MATCH (n)-[rel]-(m) 
                WHERE toLower(rel.author_id) = $user_initials
                SET rel.author_id = $user_id
                """,
                params={
                    "user_initials": user_initials.lower(),
                    "user_id": user_info.get("id", user_initials),
                },
            )
            print_counters_table(rels_summary.counters)

            updates = (
                updates
                or nodes_summary.counters.contains_updates
                or rels_summary.counters.contains_updates
            )

    return updates


async def _get_user_from_ad(user_initials: str) -> dict:
    email = f"{user_initials}@openstudybuilder.com".lower()
    logger.info("Fetching user from MS Graph: %s", email)
    user: GraphUser = await msgraph.service.get_user_by_email(email)
    logger.info("Got user: %s", user)
    if user:
        return {
            "id": user.id,
            "oid": user.id,
            "azp": None,
            "username": user.email,
            "email": user.email,
            "name": user.display_name,
        }

    return {
        "id": user_initials.lower(),
        "username": user_initials.lower(),
    }


def migrate_preferred_time_unit(db_driver, log):
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[:HAS_VERSION]->(study_value:StudyValue)
        WHERE NOT (study_value)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name:"preferred_time_unit"})
        RETURN DISTINCT study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        log.info(
            "Migrating Preferred time unit node for the following Study (%s)", study_uid
        )
        _, summary = run_cypher_query(
            db_driver,
            """
                MATCH (study_root:StudyRoot {uid:$study_uid})-[:HAS_VERSION]->(study_value:StudyValue)
                WHERE NOT (study_value)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name:"preferred_time_unit"})
                WITH distinct 
                    study_root,
                    study_value,
                    // Fetch Preferred time unit node from latest StudyValue node to copy it to older StudyValue nodes
                    head([(study_root:StudyRoot)-[:LATEST]->(:StudyValue)-[:HAS_TIME_FIELD]->(preferred_time_unit:StudyTimeField {field_name:"preferred_time_unit"}) |
                       preferred_time_unit]) AS latest_preferred_time_unit
                MERGE (study_value)-[:HAS_TIME_FIELD]->(latest_preferred_time_unit)
            """,
            params={"study_uid": study_uid},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)
    return contains_updates


def migrate_soa_preferred_time_unit(db_driver, log):
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[:HAS_VERSION]->(study_value:StudyValue)
        WHERE NOT (study_value)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name:"soa_preferred_time_unit"})
        RETURN DISTINCT study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        log.info(
            "Migrating SoA Preferred time unit node for the following Study (%s)",
            study_uid,
        )
        _, summary = run_cypher_query(
            db_driver,
            """
                MATCH (study_root:StudyRoot {uid:$study_uid})-[:HAS_VERSION]->(study_value:StudyValue)
                WHERE NOT (study_value)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name:"soa_preferred_time_unit"})
                WITH distinct 
                    study_root,
                    study_value,
                    // Fetch SoA preferred time unit node from latest StudyValue node to copy it to older StudyValue nodes
                    head([(study_root:StudyRoot)-[:LATEST]->(:StudyValue)-[:HAS_TIME_FIELD]->(soa_preferred_time_unit:StudyTimeField {field_name:"soa_preferred_time_unit"}) |
                       soa_preferred_time_unit]) AS latest_soa_preferred_time_unit
                MERGE (study_value)-[:HAS_TIME_FIELD]->(latest_soa_preferred_time_unit)
            """,
            params={"study_uid": study_uid},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)
    return contains_updates


def save_protocol_soa_snapshot_for_locked_study_versions():
    """Update SoA snapshot for all locked versions of all studies"""

    # get a list of studies
    payload = api_get(
        "/studies", params={"page_size": 1000, "total_count": True}
    ).json()
    assert payload["total"] <= 1000, "Pagination not implemented"
    study_uids = {item["uid"] for item in payload["items"]}

    for study_uid in study_uids:
        # get study versions
        payload = api_get(
            f"/studies/{study_uid}/snapshot-history", params={"page_size": 1000}
        ).json()

        for study in payload["items"]:
            study_status = study["current_metadata"]["version_metadata"]["study_status"]
            study_version = study["current_metadata"]["version_metadata"][
                "version_number"
            ]

            # on locked versions
            if study_status != "LOCKED":
                continue

            # only if the study version has no study activites
            if not _has_study_activity(study_uid, study_version):
                logger.info(
                    "Skipping study %s version %s has no study activities",
                    study_uid,
                    study_version,
                )
                continue

            # only if the study version has no protocol SoA snapshot saved
            if _has_protocol_soa_snapshot(study_uid, study_version):
                logger.info(
                    "Skipping study %s version %s already has protocol SoA snapshot",
                    study_uid,
                    study_version,
                )
                continue

            # get protocol SoA before updating the snapshot
            soa_before = api_get(
                f"/studies/{study_uid}/flowchart",
                params={
                    "study_value_version": study_version,
                    "detailed": False,
                    "operational": False,
                    "force_build": True,
                },
            ).json()

            # update SoA snapshot of the specific study version
            api_post(
                f"/studies/{study_uid}/flowchart/snapshot",
                params={"study_value_version": study_version},
                payload=None,
            )

            # get SoA snapshot of the specific study version
            soa_snapshot = api_get(
                f"/studies/{study_uid}/flowchart/snapshot",
                params={"study_value_version": study_version},
            ).json()

            assert (
                soa_snapshot == soa_before
            ), "protocol SoA snapshot does not match the inital SoA"

            # get protocol SoA after updating the snapshot
            # according to API code if protocol SoA of a locked study-version is requested,
            # always returns the snapshot
            soa_after = api_get(
                f"/studies/{study_uid}/flowchart",
                params={
                    "study_value_version": study_version,
                    "detailed": False,
                    "operational": False,
                },
            ).json()

            assert (
                soa_after == soa_before
            ), "protocol SoA snapshots do not match before and after the update"


def _has_protocol_soa_snapshot(study_uid: str, study_version: str) -> bool:
    """Check if the study version has protocol SoA snapshot saved"""
    response = api_get(
        f"/studies/{study_uid}/flowchart/snapshot",
        params={"study_value_version": study_version},
        check_ok_status=False,
    )
    assert response.status_code in {200, 404}, "Unexpected response status code"
    return response.status_code == 200


def _has_study_activity(study_uid: str, study_version: str) -> bool:
    """Check if the study version has any study activities"""
    activities = api_get(
        f"/studies/{study_uid}/study-activities",
        params={"study_value_version": study_version},
    ).json()["items"]
    return bool(len(activities))


def migrate_unify_study_visit_window_units(db_driver, log):
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT (study_root)-[:LATEST_LOCKED]-(study_value)
        MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)-[:HAS_WINDOW_UNIT]->(unit_root:UnitDefinitionRoot)-[:LATEST]->(unit_value:UnitDefinitionValue)
        // StudyVisits without timing should be excluded from check
        WHERE NOT study_visit.visit_class in ["UNSCHEDULED_VISIT", "NON_VISIT", "SPECIAL_VISIT"]
        WITH DISTINCT study_root, collect(DISTINCT unit_value.name) AS units
        WHERE size(units) > 1
        RETURN study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        log.info(
            "Refactoring StudyVisit window unit to be the same for all StudyVisits in a (%s) Study",
            study_uid,
        )
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (days_unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(days_unit_definition_value:UnitDefinitionValue {name: 'days'})
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_VISIT]
                ->(study_visit:StudyVisit)-[current_window_unit_rel:HAS_WINDOW_UNIT]->(current_unit_root:UnitDefinitionRoot)-[:LATEST]->(current_unit_value:UnitDefinitionValue)

            CALL apoc.do.case([
                // If the assigned unit is 
                current_unit_root<>days_unit_definition_root,
                'MERGE (study_visit)-[:HAS_WINDOW_UNIT]->(days_unit_definition_root)
                 SET study_visit.visit_window_max = study_visit.visit_window_max * (current_unit_value.conversion_factor_to_master / days_unit_definition_value.conversion_factor_to_master)
                 SET study_visit.visit_window_min = study_visit.visit_window_min * (current_unit_value.conversion_factor_to_master / days_unit_definition_value.conversion_factor_to_master)
                 DETACH DELETE current_window_unit_rel'
                ],
                '',
                {
                    study_visit:study_visit,
                    current_unit_root: current_unit_root,
                    current_unit_value: current_unit_value,
                    current_window_unit_rel:current_window_unit_rel,
                    days_unit_definition_root:days_unit_definition_root,
                    days_unit_definition_value:days_unit_definition_value
                })
            YIELD value
            RETURN *
            """,
            params={"study_uid": study_uid},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)
    return contains_updates

def migrate_study_selection_metadata_merge(db_driver, log):
    """
    Merge duplicated StudySoAGroup/StudyActivityGroup/StudyActivitySubGroup ndoes that are having different visibility flags set
    """
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT (study_root)-[:LATEST_LOCKED]->(study_value)
        RETURN study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        log.info(
            "Merging StudyMetadataSelection nodes for the following Study (%s)",
            study_uid,
        )
        # StudySoAGroup
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term_root:CTTermRoot)
            WHERE NOT (study_soa_group)<-[:BEFORE]-() AND NOT (study_soa_group)<-[]-(:Delete)
            WITH  
                flowchart_group_term_root,
                count(distinct flowchart_group_term_root) AS distinct_flowchart_group_count, 
                count(distinct study_soa_group) AS distinct_study_soa_group_count, 
                any(vis IN collect(study_soa_group.show_soa_group_in_protocol_flowchart) WHERE vis=true) AS is_visible
            // condition to not perform migration twice
            WHERE distinct_flowchart_group_count <> distinct_study_soa_group_count

            // leave only a few rows that will represent distinct CTTermRoots that represent chosen SoA/Flowchart group
            WITH DISTINCT flowchart_group_term_root, is_visible

            // CREATE new StudySoAGroup node for each row of a distinct flowchart_group_term_root 
            CREATE (study_soa_group_new:StudySoAGroup:StudySelection)
            MERGE (study_soa_group_counter:Counter {counterId:'StudySoAGroupCounter'})
            ON CREATE SET study_soa_group_counter:StudySoAGroupCounter, study_soa_group_counter.count=1
            WITH flowchart_group_term_root,study_soa_group_new,study_soa_group_counter, is_visible
            CALL apoc.atomic.add(study_soa_group_counter,'count',1,1) yield oldValue, newValue
            WITH flowchart_group_term_root,study_soa_group_new, toInteger(newValue) as uid_number_study_sog, is_visible
            SET study_soa_group_new.uid = "StudySoAGroup_"+apoc.text.lpad(""+(uid_number_study_sog), 6, "0")
            WITH flowchart_group_term_root, study_soa_group_new, is_visible

            // MATCH all StudyActivity nodes that had 'old' StudySoAGroups that were using a flowchart_group_term_root
            MATCH (flowchart_group_term_root)<-[:HAS_FLOWCHART_GROUP]-(study_soa_group_to_reassign)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-
                (study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
            WITH *
            ORDER BY study_activity.order ASC
            WHERE NOT (study_soa_group_to_reassign)<-[:BEFORE]-() AND NOT (study_soa_group_to_reassign)<-[]-(:Delete)

            // MERGE audit-trail entry for the newly create StudySoAGroup node that will be reused
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_soa_group_new)
            MERGE (study_value)-[:HAS_STUDY_SOA_GROUP]->(study_soa_group_new)

            // MERGE StudyActivity node with new StudySoAGroup node that will be reused between different StudyActivities
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_new)
            WITH *
            CALL apoc.do.case([
                study_soa_group_new.show_soa_group_in_protocol_flowchart IS NULL,
                'SET study_soa_group_new.show_soa_group_in_protocol_flowchart = is_visible RETURN *'
                ],
                'RETURN *',
                {
                    study_soa_group_new: study_soa_group_new,
                    study_activity:study_activity,
                    is_visible:is_visible
                })
            YIELD value

            // MERGE newly create StudySoAGroup node with distinct flowchart_group_term_root
            MERGE (study_soa_group_new)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term_root)

            WITH study_soa_group_new, study_soa_group_to_reassign,

            // Copy StudySoAFootnotes relationships from the old StudySoAGroup nodes
            apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group_to_reassign) | 
            study_soa_footnote]) as footnotes
            FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group_new))
            WITH study_soa_group_to_reassign, study_soa_group_new
            MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_to_reassign)
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_new)
            DETACH DELETE study_soa_group_to_reassign
            """,
            params={"study_uid": study_uid, "migration_desc": MIGRATION_DESC},
        )
        counters = summary.counters
        contains_updates.append(counters.contains_updates)

        # StudyActivityGroup
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->
                (study_activity_group:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            WHERE NOT (study_activity_group)<-[:BEFORE]-() AND NOT (study_activity_group)<-[]-(:Delete)

            WITH DISTINCT
                activity_group_root,
                study_soa_group,
                collect(distinct activity_group_root) AS distinct_activity_group_root, 
                collect(distinct study_activity_group) AS distinct_study_activity_group,
                any(vis IN collect(study_activity_group.show_activity_group_in_protocol_flowchart) WHERE vis=true) AS is_visible
            // condition to not perform migration twice
            WHERE size(distinct_activity_group_root) <> size(distinct_study_activity_group)

            // leave only a few rows that will represent distinct ActivityGroups in a specific StudySoAGroup
            WITH DISTINCT activity_group_root, study_soa_group, is_visible

            // CREATE new StudyActivityGroup node for each row of a distinct activity_group_root 
            CREATE (study_activity_group_new:StudyActivityGroup:StudySelection)
            MERGE (study_activity_group_counter:Counter {counterId:'StudyActivityGroupCounter'})
            ON CREATE SET study_activity_group_counter:StudyActivityGroupCounter, study_activity_group_counter.count=1
            WITH activity_group_root,study_soa_group, study_activity_group_new,study_activity_group_counter, is_visible
            CALL apoc.atomic.add(study_activity_group_counter,'count',1,1) yield oldValue, newValue
            WITH activity_group_root, study_soa_group, study_activity_group_new, toInteger(newValue) as uid_number_study_sag, is_visible
            SET study_activity_group_new.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_sag), 6, "0")
            WITH activity_group_root, study_soa_group, study_activity_group_new, is_visible

            // MATCH all StudyActivity nodes that had 'old' StudyActivityGroup inside specific StudySoAGroup that were using a activity_group_root
            MATCH (activity_group_root)-[:HAS_VERSION]->(:ActivityGroupValue)<-[:HAS_SELECTED_ACTIVITY_GROUP]-(study_activity_group_to_reassign)
                <-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
            WITH *
            ORDER BY study_activity.order ASC
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)

            // MERGE audit-trail entry for the newly create StudyActivityGroup node that will be reused
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_group_new)
            MERGE (study_value)-[:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)

            // MERGE StudyActivity node with new StudyActivityGroup node that will be reused between different StudyActivities inside same StudySoAGroup
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)
            WITH *
            CALL apoc.do.case([
                study_activity_group_new.show_activity_group_in_protocol_flowchart IS NULL,
                'SET study_activity_group_new.show_activity_group_in_protocol_flowchart = is_visible RETURN *'
                ],
                'RETURN *',
                {
                    study_activity_group_new: study_activity_group_new,
                    study_activity:study_activity,
                    is_visible:is_visible
                })
            YIELD value

            // MERGE newly create StudyActivityGroup node with distinct activity_group_value
            MATCH (activity_group_root)-[:LATEST]->(latest_activity_group_value:ActivityGroupValue)
            MERGE (study_activity_group_new)-[:HAS_SELECTED_ACTIVITY_GROUP]->(latest_activity_group_value)

            WITH study_activity_group_new, study_activity_group_to_reassign, study_activity, old_rel,

            // Copy StudySoAFootnotes relationships from the old StudyActivityGroup nodes
            apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group_to_reassign) | 
            study_soa_footnote]) as footnotes
            FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group_new))
            WITH study_activity_group_to_reassign, study_activity_group_new, study_activity, old_rel
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)
            DETACH DELETE old_rel
            """,
            params={"study_uid": study_uid, "migration_desc": MIGRATION_DESC},
        )
        counters = summary.counters
        contains_updates.append(counters.contains_updates)

        # StudyActivitySubGroup
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
                (study_activity_subgroup:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
            MATCH (study_activity_group:StudyActivityGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity)
                -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            WHERE NOT (study_activity_subgroup)<-[:BEFORE]-() AND NOT (study_activity_subgroup)<-[]-(:Delete)

            WITH DISTINCT
                activity_subgroup_root,
                study_activity_group,
                study_soa_group,
                collect(distinct activity_subgroup_root) AS distinct_activity_subgroup_root, 
                collect(distinct study_activity_subgroup) AS distinct_study_activity_subgroup,
                any(vis IN collect(study_activity_subgroup.show_activity_subgroup_in_protocol_flowchart) WHERE vis=true) AS is_visible
            // condition to not perform migration twice
            WHERE size(distinct_activity_subgroup_root) <> size(distinct_study_activity_subgroup)
            // leave only a few rows that will represent distinct ActivitySubGroups in a specific StudySoAGroup and StudyActivityGroup
            WITH DISTINCT activity_subgroup_root, study_soa_group, study_activity_group, is_visible

            // CREATE new StudyActivitySubGroup node for each row of a distinct activity_subgroup_root 
            CREATE (study_activity_subgroup_new:StudyActivitySubGroup:StudySelection)
            MERGE (study_activity_subgroup_counter:Counter {counterId:'StudyActivitySubGroupCounter'})
            ON CREATE SET study_activity_subgroup_counter:StudyActivitySubGroupCounter, study_activity_subgroup_counter.count=1
            WITH activity_subgroup_root, study_soa_group, study_activity_group, study_activity_subgroup_new,study_activity_subgroup_counter, is_visible
            CALL apoc.atomic.add(study_activity_subgroup_counter,'count',1,1) yield oldValue, newValue
            WITH activity_subgroup_root, study_soa_group, study_activity_group, study_activity_subgroup_new, toInteger(newValue) as uid_number_study_sasg, is_visible
            SET study_activity_subgroup_new.uid = "StudyActivitySubGroup_"+apoc.text.lpad(""+(uid_number_study_sasg), 6, "0")
            WITH activity_subgroup_root, study_soa_group, study_activity_group, study_activity_subgroup_new, is_visible

            // MATCH all StudyActivity nodes that had 'old' StudyActivitySubGroup inside specific StudySoAGroup and StudyActivityGroup
            MATCH (activity_subgroup_root)-[:HAS_VERSION]->(:ActivitySubGroupValue)<-[:HAS_SELECTED_ACTIVITY_SUBGROUP]-(study_activity_subgroup_to_reassign)
                <-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
            WITH *
            ORDER BY study_activity.order ASC
            MATCH (study_activity_group)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity)
                -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)

            // MERGE audit-trail entry for the newly create StudyActivitySubGroup node that will be reused
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_subgroup_new)
            MERGE (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)

            // MERGE StudyActivity node with new StudyActivitySubGroup node that will be reused between different StudyActivities inside same StudySoAGroup and StudyActivityGroup
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)
            WITH *
            CALL apoc.do.case([
                study_activity_subgroup_new.show_activity_subgroup_in_protocol_flowchart IS NULL,
                'SET study_activity_subgroup_new.show_activity_subgroup_in_protocol_flowchart = is_visible RETURN *'
                ],
                'RETURN *',
                {
                    study_activity_subgroup_new: study_activity_subgroup_new,
                    study_activity:study_activity,
                    is_visible:is_visible
                })
            YIELD value

            // MERGE newly create StudyActivitySubGroup node with distinct activity_subgroup_value
            MATCH (activity_subgroup_root)-[:LATEST]->(latest_activity_subgroup_value:ActivitySubGroupValue)
            MERGE (study_activity_subgroup_new)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(latest_activity_subgroup_value)

            WITH study_activity_subgroup_new, study_activity_subgroup_to_reassign, study_activity, old_rel,
            // Copy StudySoAFootnotes relationships from the old StudyActivitySubGroup nodes
            apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_to_reassign) | 
            study_soa_footnote]) as footnotes
            FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new))
            WITH study_activity_subgroup_to_reassign, study_activity_subgroup_new, study_activity, old_rel
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)
            DETACH DELETE old_rel
            """,
            params={"study_uid": study_uid, "migration_desc": MIGRATION_DESC},
        )
        counters = summary.counters
        contains_updates.append(counters.contains_updates)

    return any(contains_updates)

if __name__ == "__main__":
    main()
