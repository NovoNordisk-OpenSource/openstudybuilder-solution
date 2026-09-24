import csv
from os import path

AUTHOR_ID = "CDISC_IMPORT"


def update_codelist_names_managed_by_novo_nordisk(tx, csv_import_directory):
    with open(
        path.join(csv_import_directory, "sponsor_codelist_names.csv"), "r"
    ) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",", quotechar='"')

        # skip the header row
        next(csv_reader, None)

        for row in csv_reader:
            concept_id = row[0]
            sponsor_preferred_name = row[2]
            use_row = row[3]

            if use_row.lower() != "yes":
                pass

            result = tx.run(
                """
                MATCH (codelist_root:CTCodelistRoot{uid: $concept_id})-[:HAS_NAME_ROOT]->(codelist_name_root)

                // check if there is an existing value with the preferred name
                OPTIONAL MATCH (codelist_name_root)-[:LATEST]->(codelist_name_value)
                // only do the update if the db value is not set at all
                // or if the db value is different from the one specified in the csv file
                RETURN 
                    codelist_name_value IS NULL OR
                    codelist_name_value.name <> $sponsor_preferred_name
                    AS update_needed
                """,
                concept_id=concept_id,
                sponsor_preferred_name=sponsor_preferred_name,
            ).single()

            is_update_needed = result["update_needed"] if result is not None else False
            # print("  Updating " + str(len(rows_to_update)) + " CTCodelistNameValue entries.")
            # print(concept_id + ": " + str(is_update_needed))

            if is_update_needed:
                # TODO make sure that only the latest CTCodelistNameValue and only the latest CTTermNameValue nodes are marked as template parameter
                # TODO discuss the exact rules with Mikkel and co.

                _result = tx.run(
                    """
                    MATCH (:CTCodelistRoot{uid: $concept_id})-[:HAS_NAME_ROOT]->(codelist_name_root)
                    OPTIONAL MATCH (codelist_name_root)-[latest_final:LATEST_FINAL]->(old_codelist_name_value)
                    OPTIONAL MATCH (codelist_name_root)-[latest_hv:HAS_VERSION {status: "Final"}]->(old_codelist_name_value) WHERE latest_hv.end_date IS NULL
                    WITH codelist_name_root, latest_final, latest_hv, old_codelist_name_value, latest_hv.version AS version

                    // if there is a previous Final version, close this
                    FOREACH (not_used IN CASE WHEN latest_hv IS NOT NULL THEN [1] ELSE [] END |
                        CREATE (codelist_name_root)-[v:HAS_VERSION]->(old_codelist_name_value)
                        SET v.end_date = datetime()
                    )
                    FOREACH (not_used IN CASE WHEN latest_final IS NOT NULL THEN [1] ELSE [] END |
                        DELETE latest_final
                    )

                    WITH codelist_name_root, old_codelist_name_value, version
                    OPTIONAL MATCH (codelist_name_root)-[latest:LATEST]->(old_codelist_name_value)
                    FOREACH (not_used IN CASE WHEN latest IS NOT NULL THEN [1] ELSE [] END |
                        DELETE latest
                    )

                    // create the new LATEST and LATEST_FINAL relationships
                    WITH codelist_name_root, version, old_codelist_name_value
                    CREATE (codelist_name_root)-[:LATEST]->(codelist_name_value:CTCodelistNameValue)
                    CREATE (codelist_name_root)-[:LATEST_FINAL]->(codelist_name_value:CTCodelistNameValue)
                    CREATE (codelist_name_root)-[:HAS_VERSION {
                        start_date:         datetime(),
                        status:             'Final',
                        version:             toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
                        change_description: 'Update after importing from CDISC',
                        author_id:          $author_id
                    }]->(codelist_name_value)
                    SET codelist_name_value.name = $sponsor_preferred_name
                    
                    RETURN DISTINCT
                        id(codelist_name_value) AS new_id,
                        id(old_codelist_name_value) AS old_id
                    """,
                    concept_id=concept_id,
                    sponsor_preferred_name=sponsor_preferred_name,
                    author_id=AUTHOR_ID,
                )

                #
                # tx.run(
                #     """
                #     MATCH (
                #     """,
                #     new_id=new_id,
                #     old_id=old_id
                # )

        # result = tx.run(
        #     """
        #     UNWIND $csv_data AS row
        #         WITH collect(row.sponsor_preferred_name) AS expected_name_values
        #         OPTIONAL MATCH (name_value:CTCodelistNameValue)
        #         WHERE name_value.name IN expected_name_values
        #         RETURN expected_name_values, collect(name_value.name) AS actual_name_values
        #     """,
        #     csv_data = csv_data
        # ).single()
        #
        # missing_names = [name for name in result["expected_name_values"] if
        #                  not name in result["actual_name_values"]]
        # if missing_names:
        #     print("WARNING: The following codelist names (CTCodelistNameValue nodes) haven't been found:")
        #     print(missing_names)


# TODO fix versioning, check for instance:
# MATCH path=(:CTTermRoot{uid: 'C38272'})-->()-->()
# RETURN path
def update_term_names_managed_by_novo_nordisk(tx, csv_import_directory):
    with open(
        path.join(csv_import_directory, "sponsor_term_names.csv"), "r"
    ) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",", quotechar='"')

        # skip the header row
        next(csv_reader, None)

        for row in csv_reader:
            concept_id = row[12]
            sponsor_preferred_name = row[4]
            sponsor_preferred_name_sentence_case = row[5]

            result = tx.run(
                """
                MATCH (term_root:CTTermRoot{uid: $concept_id})-[:HAS_NAME_ROOT]->(term_name_root)
    
                // check if there is an existing value with the preferred name
                OPTIONAL MATCH (term_name_root)-[:LATEST]->(term_name_value)
                // only do the update if the db value is not set at all
                // or if the db value is different from the one specified in the csv file
                RETURN
                    term_name_value IS NULL OR
                    term_name_value.name <> $sponsor_preferred_name OR
                    term_name_value.name_sentence_case <> $sponsor_preferred_name_sentence_case
                    AS update_needed
                """,
                concept_id=concept_id,
                sponsor_preferred_name=sponsor_preferred_name,
                sponsor_preferred_name_sentence_case=sponsor_preferred_name_sentence_case,
            ).single()

            is_update_needed = result["update_needed"] if result is not None else False

            if is_update_needed:
                tx.run(
                    """
                    MATCH (term_root:CTTermRoot{uid: $concept_id})-[:HAS_NAME_ROOT]->(term_name_root)
                    OPTIONAL MATCH (term_name_root)-[latest_final:LATEST_FINAL]->(old_term_name_value)
                    OPTIONAL MATCH (term_name_root)-[latest_hv:HAS_VERSION {status: "Final"}]->(old_term_name_value) WHERE latest_hv.end_date IS NULL
                    WITH term_name_root, latest_final, latest_hv, old_term_name_value, latest_hv.version AS version
                    
                    // if there is a previous Final version, close this
                    FOREACH (not_used IN CASE WHEN latest_hv IS NOT NULL THEN [1] ELSE [] END |
                        SET v.end_date = datetime()
                    )
                    FOREACH (not_used IN CASE WHEN latest_final IS NOT NULL THEN [1] ELSE [] END |
                        DELETE latest_final
                    )
                    
                    WITH term_name_root, old_term_name_value, version
                    OPTIONAL MATCH (term_name_root)-[latest:LATEST]->(old_term_name_value)
                    FOREACH (not_used IN CASE WHEN latest IS NOT NULL THEN [1] ELSE [] END |
                        DELETE latest
                    )
    
                    // create the new LATEST and LATEST_FINAL relationships
                    WITH term_name_root, version
                    CREATE (term_name_root)-[:LATEST]->(term_name_value:CTTermNameValue)
                    CREATE (term_name_root)-[:LATEST_FINAL]->(term_name_value:CTTermNameValue)
                    CREATE (term_name_root)-[:HAS_VERSION {
                        start_date:         datetime(),
                        status:             'Final',
                        version:            toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
                        change_description: 'Update after importing from CDISC',
                        author_id:          $author_id
                    }]->(term_name_value)
                    SET term_name_value.name = $sponsor_preferred_name,
                        term_name_value.name_sentence_case = $sponsor_preferred_name_sentence_case
                    """,
                    concept_id=concept_id,
                    sponsor_preferred_name=sponsor_preferred_name,
                    sponsor_preferred_name_sentence_case=sponsor_preferred_name_sentence_case,
                    author_id=AUTHOR_ID,
                )


def flag_specific_codelists_as_parameters(tx, csv_import_directory):
    with open(
        path.join(csv_import_directory, "codelist_parameter_names.csv"), "r"
    ) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",", quotechar='"')
        csv_data = [{"concept_id": row[0]} for row in csv_reader]

        tx.run(
            """
            UNWIND $csv_data AS row
                MATCH (codelist_root:CTCodelistRoot{uid: row.concept_id})-[:HAS_NAME_ROOT]->()-[:LATEST]->(codelist_name_value)
                SET
                    codelist_name_value:TemplateParameter
                WITH codelist_name_value
                MATCH (codelist_name_value)<-[:LATEST]-()<-[:HAS_NAME_ROOT]-()-[:HAS_TERM]->()-[:HAS_NAME_ROOT]->(term_name_root)
                SET term_name_root:TemplateParameterValueRoot
                MERGE (codelist_name_value)-[:HAS_VALUE]->(term_name_root)
                WITH term_name_root
                MATCH (term_name_root)-[:LATEST]->(term_name_value)
                SET term_name_value:TemplateParameterValue
            """,
            csv_data=csv_data,
        )

        # result = tx.run(
        #     """
        #     LOAD CSV WITH HEADERS FROM 'file:///' + $csv_file AS row
        #     WITH collect(row.CODELIST_NAME) AS expected_name_values
        #     OPTIONAL MATCH (name_value:CTCodelistNameValue)
        #     WHERE name_value.name IN expected_name_values AND name_value:TemplateParameter
        #     RETURN expected_name_values, collect(name_value.name) AS actual_name_values
        #     """,
        #     csv_file=csv_file
        # ).single()
        #
        # missing_names = [name for name in result["expected_name_values"] if
        #                  not name in result["actual_name_values"]]
        # if missing_names:
        #     print(
        #         "WARNING: The following codelist names (CTCodelistNameValue nodes) haven't been flagged as template parameters:")
        #     print(missing_names)


def run_novo_nordisk_adjustments(
    mdr_neo4j_driver, mdr_db_name, csv_import_directory, author_id
):
    global AUTHOR_ID
    AUTHOR_ID = author_id

    with mdr_neo4j_driver.session(database=mdr_db_name) as session:
        with session.begin_transaction() as tx:
            print("    - Updating the sponsor codelist names.")
            update_codelist_names_managed_by_novo_nordisk(tx, csv_import_directory)

            print("    - Updating the sponsor term names.")
            update_term_names_managed_by_novo_nordisk(tx, csv_import_directory)

            # print("    - Flagging selected codelists as parameters.")
            # flag_specific_codelists_as_parameters(tx, csv_import_directory)

            tx.commit()

        session.close()
