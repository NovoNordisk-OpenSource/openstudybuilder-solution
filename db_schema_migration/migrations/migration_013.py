"""Schema migrations needed for release 1.14 to PROD post June 2025."""

import json
import os

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import (
    api_get_paged,
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-1.14"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_visit_group_into_node(DB_DRIVER, logger)


def migrate_visit_group_into_node(db_driver, log):
    contain_updates = []
    # get a list of studies
    payload = api_get_paged(
        "/studies",
        page_size=50,
        params={
            "sort_by": json.dumps({"uid": True}),
        },
    )
    studies = payload["items"]
    for study in studies:
        study_uid = study["uid"]
        study_number = study["current_metadata"]["identification_metadata"][
            "study_number"
        ]
        log.info(
            "Refactoring :StudyVisit consecutive_visit_group property into separate StudyVisitGroup node in a (%s) Study",
            study_number,
        )

        study_visit_in_consecutive_group, _ = run_cypher_query(
            db_driver,
            """
            MATCH (:StudyRoot{uid:$study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
            WHERE NOT (study_visit)-[:BEFORE]-() AND study_visit.consecutive_visit_group IS NOT NULL
            WITH study_visit.consecutive_visit_group as group_name, collect(distinct study_visit.uid) as grouped_visits
            RETURN *
        """,
            params={"study_uid": study_uid},
        )

        for item in study_visit_in_consecutive_group:
            consecutive_visit_group_name = item[0]
            study_visits_in_group = item[1]
            # Create StudyVisitGroup node for each unique VisitGroup in a Study
            created_visit_group, visit_group_creation_summary = run_cypher_query(
                db_driver,
                """
                CREATE (visit_group:StudyVisitGroup {group_format:'range'})

                MERGE (visit_group_counter:Counter {counterId:'StudyVisitGroupCounter'})
                ON CREATE SET visit_group_counter:StudyVisitGroupCounter, visit_group_counter.count=1
                WITH visit_group,visit_group_counter
                CALL apoc.atomic.add(visit_group_counter,'count',1,1) yield oldValue, newValue
                WITH visit_group, toInteger(newValue) as uid_number_study_visit_group
                SET visit_group.uid = "StudyVisitGroup_"+apoc.text.lpad(""+(uid_number_study_visit_group), 6, "0")

                RETURN visit_group.uid
            """,
                params={"visit_group_name": consecutive_visit_group_name},
            )
            print_counters_table(visit_group_creation_summary.counters)
            contain_updates.append(
                visit_group_creation_summary.counters.contains_updates
            )

            if not created_visit_group:
                raise RuntimeError(
                    f"The StudyVisitGroup for name {consecutive_visit_group_name} was not created"
                )
            visit_group_uid = created_visit_group[0][0]

            # Update each StudyVisit in a group to link to new StudyVisitGroup node
            for study_visit in study_visits_in_group:

                _, visit_group_relationship_summary = run_cypher_query(
                    db_driver,
                    """
                    MATCH (study_visit:StudyVisit {uid:$study_visit_uid})
                    WHERE study_visit.consecutive_visit_group IS NOT NULL AND NOT (study_visit)-[:BEFORE]-()
                    MATCH (visit_group:StudyVisitGroup {uid:$visit_group_uid})
                    MERGE (study_visit)-[:IN_VISIT_GROUP]->(visit_group)
                    REMOVE study_visit.consecutive_visit_group
                    """,
                    params={
                        "study_visit_uid": study_visit,
                        "visit_group_uid": visit_group_uid,
                    },
                )
                print_counters_table(visit_group_relationship_summary.counters)
                contain_updates.append(
                    visit_group_relationship_summary.counters.contains_updates
                )

    return contain_updates


if __name__ == "__main__":
    main()
