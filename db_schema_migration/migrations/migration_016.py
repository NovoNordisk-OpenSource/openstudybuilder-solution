"""Schema migrations for CT migration"""

import os

from neo4j import SummaryCounters

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
MIGRATION_DESC = "schema-migration-ct"

NON_CT_LABELS_SELECTION = (
    "!(CTTermRoot|CTCodelistRoot|CTTermNameRoot|CTTermAttributesRoot|Library)"
)


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])
    remove_odm_data(DB_DRIVER, logger)
    correct_activity_item_ct_mapping(DB_DRIVER, logger)
    migrate_test_name_code(DB_DRIVER, logger)
    migrate_ct(DB_DRIVER, logger)

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)


def remove_odm_data(db_driver, log):
    """
    Cleanup the database by removing ODM data.
    This data is hard to migrate, and is not yet used.
    We remove it from the database for now, to be re-imported at a later time.
    """

    contains_updates = False
    for entity in [
        "OdmDescription",
        "OdmAlias",
        "OdmCondition",
        "OdmMethod",
        "OdmFormalExpression",
        "OdmForm",
        "OdmItemGroup",
        "OdmItem",
        "OdmStudyEvent",
        "OdmVendorNamespace",
        "OdmVendorAttribute",
        "OdmVendorElement",
    ]:
        log.info(
            f"Cleaning up the database - Removing {entity}Root and {entity}Value nodes"
        )
        _, summary = run_cypher_query(
            db_driver,
            f"""
            MATCH (r:{entity}Root)--(v:{entity}Value)
            DETACH DELETE r, v
            """,
        )
        print_counters_table(summary.counters)
        contains_updates = contains_updates or summary.counters.contains_updates
    return contains_updates


def correct_activity_item_ct_mapping(db_driver, log) -> bool:
    """
    Correct activity items for test name and code that have mistakenly
    been linked to the wrong terms.
    """
    log.info("Correcting Activity Item CT Mapping")

    # Correct the wrongly linked milligram unit instead of magnesium measurement test
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (:CTCodelistRoot{uid: "C65047"})-[:HAS_TERM]->(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]->(:CTTermAttributesValue {code_submission_value: "MG"})
        WITH DISTINCT tr
        MATCH (aicv:ActivityItemClassValue {name: "test_name_code"})<-[:LATEST]-(aicr:ActivityItemClassRoot)-[:HAS_ACTIVITY_ITEM]->(ai:ActivityItem)-[ht:HAS_CT_TERM]->(t:CTTermRoot {uid: "C28253_mg"})
        DELETE ht
        WITH tr, ai
        MERGE (ai)-[:HAS_CT_TERM]->(tr)
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    # Replace the wrongly linked Thickness test for CV instances with the correct test from CVTEST / CVTESTCD
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (:CTCodelistRoot{uid: "C101847"})-[:HAS_TERM]->(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]->(:CTTermAttributesValue {code_submission_value: "THCKEVD"})
        WITH DISTINCT tr

        MATCH (aicv:ActivityItemClassValue)<-[:LATEST]-(aicr:ActivityItemClassRoot)-[:HAS_ACTIVITY_ITEM]->(ai:ActivityItem)-[ht:HAS_CT_TERM]->(:CTTermRoot)--(:CTTermAttributesRoot)-[:LATEST]->(:CTTermAttributesValue {concept_id: "C41145"})
        WHERE (ai)<-[:CONTAINS_ACTIVITY_ITEM]-(:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(:ActivityItem)-[:HAS_CT_TERM]->(:CTTermRoot {uid: "C102605_CV"}) AND aicv.name IN ["test_name", "test_code"]
        DELETE ht
        WITH tr, ai
        MERGE (ai)-[:HAS_CT_TERM]->(tr)
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates
    return contains_updates


def migrate_test_name_code(db_driver, log) -> bool:
    """
    Migrate the test_name_code activity items by splitting them into separate
    test_name and test_code items.
    """

    log.info("Migrating test_name_code activity items to test_name and test_code")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (tnicr:ActivityItemClassRoot)-->(:ActivityItemClassValue {name:"test_name"})
        MATCH (tcicr:ActivityItemClassRoot)-->(:ActivityItemClassValue {name:"test_code"})
        WITH DISTINCT tnicr, tcicr
        MATCH (aiv:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]-(ai:ActivityItem)<--(aicr:ActivityItemClassRoot)-->(:ActivityItemClassValue {name:"test_name_code"})
        CALL {
            WITH ai, aiv, tnicr, tcicr
            MATCH (ai)-[:HAS_CT_TERM]->(tr:CTTermRoot)
            MERGE (aiv)-[:CONTAINS_ACTIVITY_ITEM]->(tnai:ActivityItem {is_adam_param_specific: ai.is_adam_param_specific})<-[:HAS_ACTIVITY_ITEM]-(tnicr)
            MERGE (tnai)-[:HAS_CT_TERM]->(tr)
            MERGE (aiv)-[:CONTAINS_ACTIVITY_ITEM]->(tcai:ActivityItem {is_adam_param_specific: ai.is_adam_param_specific})<-[:HAS_ACTIVITY_ITEM]-(tcicr)
            MERGE (tcai)-[:HAS_CT_TERM]->(tr)
            DETACH DELETE ai
        } IN TRANSACTIONS OF 100 ROWS
        WITH DISTINCT aicr
        MATCH (aicr)-->(aicv:ActivityItemClassValue)
        DETACH DELETE aicr, aicv
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates
    return contains_updates


def migrate_ct(db_driver, log) -> bool:
    result, _ = run_cypher_query(
        db_driver,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label CONTAINS "_sideload")
        RETURN count(DISTINCT n) AS count
        """,
    )

    if result[0]["count"] == 0:
        log.info(
            "No sideloaded elements found. Skipping migration. Run the CT import with sideload option on before re-trying."
        )
        return False

    contains_updates = []
    # Sideload elements
    sideload_sponsor_codelists(db_driver, log)
    sideload_sponsor_terms(db_driver, log)
    migrate_had_term_only_terms(db_driver, log)

    # Get test_name/test_code mapping before migrating anything else
    (
        test_code_mapping,
        test_name_mapping,
        manual_mapping_necessary,
    ) = get_test_name_code_mapping(db_driver, log)

    # Migrate terms
    # CDISC terms
    contains_updates.append(
        create_cttermcontext_for_single_codelist_terms(db_driver, log)
    )
    contains_updates.append(
        create_cttermcontext_for_multiple_codelist_terms(db_driver, log)
    )
    contains_updates.append(create_cttermcontext_for_references_term(db_driver, log))
    contains_updates.append(
        create_cttermcontext_for_activity_item_terms(
            db_driver,
            log,
            test_code_mapping,
            test_name_mapping,
            manual_mapping_necessary,
        )
    )

    # Sponsor Terms
    contains_updates.append(
        create_cttermcontext_for_single_codelist_terms_sponsor(db_driver, log)
    )
    contains_updates.append(
        create_cttermcontext_for_multiple_codelist_terms_sponsor(db_driver, log)
    )
    contains_updates.append(
        create_cttermcontext_for_activity_item_terms_sponsor(db_driver, log)
    )

    # Migrate props containing CT UIDs
    contains_updates.append(migrate_ct_uid_properties(db_driver, log))

    # Term-Term relationships
    contains_updates.append(migrate_term_to_term_relationships(db_driver, log))

    # Migrate template parameter USES_VALUE relationships
    contains_updates.append(migrate_uses_value(db_driver, log))

    # Mark template parameter value terms
    contains_updates.append(mark_cdisc_template_parameter_terms(db_driver, log))

    # Mark template parameter codelists
    contains_updates.append(mark_cdisc_template_parameter_codelists(db_driver, log))

    # Migrate Sponsor CT packages
    contains_updates.append(migrate_sponsor_ct_packages(db_driver, log))

    # Remove old CT and re-label nodes
    contains_updates.append(remove_old_ct_and_relabel_nodes(db_driver, log))

    # Migrate new CDISC Epoch terms
    contains_updates.append(migrate_cdisc_epoch_terms(db_driver, log))

    # Cleanup database of not-relevant-anymore elements
    contains_updates.append(cleanup(db_driver, log))

    return any(contains_updates)


def sideload_sponsor_codelists(db_driver, log):
    log.info("Adding sideload label to sponsor codelists")

    run_cypher_query(
        db_driver,
        """
        MATCH (nv:CTCodelistNameValue)<--(nr:CTCodelistNameRoot)<--(cr:CTCodelistRoot)-->(ar:CTCodelistAttributesRoot)-->(av:CTCodelistAttributesValue)
        WHERE EXISTS ((:Library{name:"Sponsor"})-[:CONTAINS_CODELIST]->(cr))
        WITH DISTINCT nv, nr, cr, ar, av
        SET nv:CTCodelistNameValue_sideload,
            nr:CTCodelistNameRoot_sideload,
            cr:CTCodelistRoot_sideload,
            ar:CTCodelistAttributesRoot_sideload,
            av:CTCodelistAttributesValue_sideload
        WITH DISTINCT cr
        MATCH (cr)<-[:HAS_CODELIST]-(cat:CTCatalogue)
        MATCH (new_cat:CTCatalogue_sideload)
        WHERE new_cat.name=cat.name
        MERGE (cr)<-[:HAS_CODELIST]-(new_cat)
        """,
    )

    # Migrate CDISC terms - Sponsor codelist relationships
    # This reuses CTCodelistTerm nodes connected to CDISC terms and their CDISC codelist
    run_cypher_query(
        db_driver,
        """
        MATCH (lib_cl:Library)–[:CONTAINS_CODELIST]->(cl:CTCodelistRoot)-[has_term:HAS_TERM]->(us:CTTermRoot)<-[:CONTAINS_TERM]-(lib_t:Library)
        WHERE lib_cl.name = "Sponsor" AND lib_t.name <> "Sponsor"
        MATCH (av:CTTermAttributesValue)--(ar:CTTermAttributesRoot)--(us)
        MATCH (new_us:CTTermRoot_sideload)
        WHERE new_us.uid=us.concept_id
        MATCH (ct:CTCodelistTerm_sideload {submission_value: av.code_submission_value})-[:HAS_TERM_ROOT]->(new_us)
        WITH DISTINCT ct, has_term, cl
        MERGE (ct)<-[new_ht:HAS_TERM]-(cl)
        SET new_ht += properties(has_term)
        RETURN count(DISTINCT new_ht)
        """,
    )


def sideload_sponsor_terms(db_driver, log):
    log.info("Migrating Sponsor terms")

    # Firstly, rename HAD_TERM relationship to match new model for CDISC terms
    run_cypher_query(
        db_driver,
        """
            MATCH (:CTCodelistRoot)-[r:HAD_TERM]->(:CTTermRoot)<-[:CONTAINS_TERM]-(lib:Library)
            WHERE lib.name = "Sponsor"
            CALL apoc.refactor.setType(r, "HAS_TERM")
            YIELD input, output
            RETURN count(*)
        """,
    )

    # Then, migrate terms and sideload them
    run_cypher_query(
        db_driver,
        """
            MATCH (cl:CTCodelistRoot)-[ht:HAS_TERM]->(us:CTTermRoot)<-[:CONTAINS_TERM]-(lib:Library)
            WHERE lib.name = "Sponsor"
            MATCH (av:CTTermAttributesValue)--(ar:CTTermAttributesRoot)--(us)--(nr:CTTermNameRoot)--(nv:CTTermNameValue)
            MATCH (new_cl:CTCodelistRoot_sideload)
            WHERE new_cl.uid = cl.uid
            MERGE (ct:CTCodelistTerm_sideload_temp {submission_value: av.code_submission_value})
            MERGE (us)<-[:HAS_TERM_ROOT]-(ct)
            MERGE (ct)<-[new_ht:HAS_TERM]-(new_cl)
            SET new_ht += properties(ht)
            SET nv:CTTermNameValue_sideload,
                nr:CTTermNameRoot_sideload,
                us:CTTermRoot_sideload,
                ar:CTTermAttributesRoot_sideload,
                av:CTTermAttributesValue_sideload,
                ct:CTCodelistTerm_sideload
            REMOVE ct:CTCodelistTerm_sideload_temp
            RETURN count(DISTINCT ct)
        """,
    )


def migrate_had_term_only_terms(db_driver, log):
    log.info("Migrating HAD_TERM only terms")
    run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel]-(them:!(CTTermRoot|CTCodelistRoot|CTTermNameRoot|CTTermAttributesRoot|Library))
        MATCH (cl:CTCodelistRoot)-[r:HAD_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE NOT EXISTS ((:CTCodelistRoot)-[:HAS_TERM]->(us))
        CALL apoc.refactor.setType(r, "HAS_TERM")
        YIELD input, output
        RETURN count(*)
        """,
    )


def create_cttermcontext_for_single_codelist_terms(db_driver, log):
    """
    Create CTTermContext for terms in a single codelist.
    This looks up all terms that are in a single codelist and targeted by a non-CT node,
    then matches the same term and its codelist in the sideloaded CT,
    creates a CTTermContext, and refactors the relationship to point to the new context node.
    """
    log.info("Creating CTTermContext for terms in a single codelist")
    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (us:CTTermRoot)<-[migrate_rel]-(them:{NON_CT_LABELS_SELECTION})
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl
        WITH us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists = 1
        UNWIND codelists AS cl
        MATCH (new_us:CTTermRoot_sideload)
        MATCH (new_cl:CTCodelistRoot_sideload)
        WHERE new_us.uid=us.concept_id AND new_cl.uid=cl.uid
        WITH new_us, new_cl, migrate_rel
        CALL {{
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        }} IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
    """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def create_cttermcontext_for_multiple_codelist_terms(db_driver, log):
    """
    Create CTTermContext for terms in multiple codelists.
    This looks up all terms that are in multiple codelists and targeted by a non-CT node,
    then disambiguates the codelist based on rules,
    then matches the term and the picked codelist in the sideloaded CT,
    creates a CTTermContext, and refactors the relationship to point to the new context node.

    Notes: In this case, codelists can be Sponsor ones, hence the need to first "sideload" them.
    This covers all cases except two - REFERENCES_TERM and HAS_CODELIST_TERM, covered in the next function.
    """
    log.info("Creating CTTermContext for terms in multiple codelists")
    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (us:CTTermRoot)<-[migrate_rel:!(REFERENCES_TERM|HAS_CODELIST_TERM|HAS_CT_TERM)]-(them:{NON_CT_LABELS_SELECTION})
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl
        WITH us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        UNWIND codelists AS cl
        WITH us, migrate_rel, cl,
        CASE type(migrate_rel)
            WHEN "HAS_CT_DIMENSION" THEN "Unit Dimension"
            WHEN "HAS_DATA_DOMAIN", "HAS_SDTM_DOMAIN" THEN "SDTM Domain Abbreviation"
            WHEN "HAS_CT_UNIT" THEN "Unit"
            WHEN "HAS_REASON_FOR_NULL_VALUE" THEN "Null Flavor Reason"
            WHEN "HAS_EPOCH_SUB_TYPE" THEN "Epoch Sub Type"
            WHEN "HAS_EPOCH_TYPE" THEN "Epoch Type"
            WHEN "HAS_EPOCH" THEN "Epoch"
            WHEN "HAS_DOSAGE_FORM" THEN "Pharmaceutical Dosage Form"
            WHEN "HAS_ROUTE_OF_ADMINISTRATION" THEN "Route of Administration"
            WHEN "HAS_CONFIGURED_TERM" THEN "Trial Summary Parameter Test Code"
            WHEN "HAS_OBJECTIVE_LEVEL" THEN "Objective Level"
            WHEN "HAS_ENDPOINT_LEVEL" THEN "Endpoint Level"
            WHEN "HAS_TYPE" THEN "Criteria Type"
            WHEN "HAS_CATEGORY" THEN "Objective Category"
            WHEN "HAS_DOSE_FREQUENCY" THEN "Frequency"
            WHEN "HAS_UNIT_SUBSET" THEN "Unit Subset"
            ELSE NULL
            END AS target_codelist_name
        MATCH (new_us:CTTermRoot_sideload)
        MATCH (new_cl:CTCodelistRoot_sideload)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot_sideload)-->(target_cl:CTCodelistNameValue_sideload)
        WHERE target_cl.name=target_codelist_name AND new_us.uid=us.concept_id
        WITH DISTINCT new_us, new_cl, migrate_rel, target_codelist_name
        CALL {{
           WITH new_us, new_cl, migrate_rel
           MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
           WITH ctx_new, new_us, new_cl, migrate_rel
           CALL apoc.refactor.to(migrate_rel, ctx_new)
           YIELD output
           RETURN output AS migrated_rel
        }} IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
    """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def create_cttermcontext_for_references_term(db_driver, log):
    """
    Create CTTermContext for terms in multiple codelists.
    This looks up all terms that are in multiple codelists and targeted by a DatasetVariable node,
    then disambiguates the codelist,
    then matches the term and the picked codelist in the sideloaded CT,
    creates a CTTermContext, and refactors the relationship to point to the new context node.
    """

    log.info(
        "Creating CTTermContext for terms in multiple codelists targeted by DatasetVariable"
    )

    # First, migrate terms targeted by the DOMAIN variable
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel:REFERENCES_TERM]-(them:DatasetVariableInstance)<--(:DatasetVariable {uid: "DOMAIN"})
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        MATCH (new_us:CTTermRoot_sideload)
        MATCH (new_cl:CTCodelistRoot_sideload)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot_sideload)-->(target_cl:CTCodelistNameValue_sideload)
        WHERE target_cl.name="SDTM Domain Abbreviation" AND new_us.uid=us.concept_id
        WITH DISTINCT new_us, new_cl, migrate_rel
        CALL {
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(migrated_rel)
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    # Then, migrate other terms targeted by DatasetVariable
    # This is a bit more complex, as we need to disambiguate the codelist
    # But we found that there is always at least another term targeted by the same variable
    # And belonging to a single codelist : use that one to disambiguate
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel:REFERENCES_TERM]-(them:DatasetVariableInstance)<--(dv:DatasetVariable WHERE NOT dv.uid="DOMAIN")
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        MATCH (them)-[:REFERENCES_TERM]->(:CTTermContext)-->(new_cl:CTCodelistRoot_sideload)
        MATCH (new_us:CTTermRoot_sideload)
        WHERE new_us.uid=us.concept_id
        WITH DISTINCT new_us, new_cl, migrate_rel
        CALL {
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(migrated_rel)
    """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return contains_updates


def _extract_test_name_code_mapping(submission_values: list[str]) -> tuple[str, str]:
    # Example: ["LBTEST", "LBTESTCD"] or ["ESS01TC", "ESS01TN"]
    # Pick the one ending with CD or TC
    if submission_values[0].endswith("CD") or submission_values[0].endswith("TC"):
        return submission_values[0], submission_values[1]
    return submission_values[1], submission_values[0]


def get_test_name_code_mapping(
    db_driver, log
) -> tuple[dict[str, str], dict[str, str], list[str]]:
    # Extract mapping for test_name/test_code before migrating other ActivityItems
    # Because it would migrate the Domain terms, which we need to disambiguate
    log.info(
        "Getting information for test_name/test_code activity items before migrating anything else"
    )
    test_code_mapping = {}
    test_name_mapping = {}
    manual_mapping_necessary = []
    results, _ = run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel:HAS_CT_TERM]-(them:ActivityItem)<--(:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue WHERE aicv.name IN ["test_name", "test_code"])
        OPTIONAL MATCH (them)<-[:CONTAINS_ACTIVITY_ITEM]-()-->(other_ai:ActivityItem)<--(:ActivityItemClassRoot)-[:LATEST]->(:ActivityItemClassValue {name: "domain"})
        OPTIONAL MATCH (other_ai)-[:HAS_CT_TERM]->(:CTTermRoot)-->(:CTTermAttributesRoot)-->(other_term_av:CTTermAttributesValue)
        MATCH (av:CTCodelistAttributesValue)<-[:LATEST]-(ar:CTCodelistAttributesRoot)<--(cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl, av, aicv.name AS aicv, other_term_av.code_submission_value AS domain
        WITH us, migrate_rel, them, collect(DISTINCT av.submission_value) AS cl_subval, collect(DISTINCT av.name) AS cl_name, collect(DISTINCT cl) AS codelists, count(DISTINCT cl) AS number_codelists, aicv, domain
        WHERE number_codelists > 1
        RETURN DISTINCT us.concept_id AS term, cl_subval, domain
        """,
    )
    for row in results:
        if len(row[1]) == 2:
            # It will be one like ["LBTEST", "LBTESTCD"] or ["ESS01TC", "ESS01TN"]
            term_code, term_name = _extract_test_name_code_mapping(row[1])
            test_code_mapping[row[0]] = term_code
            test_name_mapping[row[0]] = term_name
            log.debug(f"Mapped {row[0]} to {term_code} / {term_name}")
        elif len(row[1]) > 2 and row[2]:
            domain = row[2]
            # Some domains require an override
            if row[2] == "MK":
                domain = "MU"
                log.debug(f"Overriding MK domain to MU for {row[0]}")
            # Find the 2 codelists with the submission values starting with domain
            domain_codelists = [
                codelist for codelist in row[1] if codelist.startswith(domain)
            ]
            # For VS domain, also look for SVSTST / SVSTSTCD codelists
            if len(domain_codelists) == 0 and domain == "VS":
                domain_codelists = [
                    codelist for codelist in row[1] if codelist.startswith("SVS")
                ]
            log.debug(f"All codelists: {row[1]} Filtered codelists: {domain_codelists}")
            if len(domain_codelists) >= 2:
                term_code, term_name = _extract_test_name_code_mapping(domain_codelists)
                test_code_mapping[row[0]] = term_code
                test_name_mapping[row[0]] = term_name
                log.debug(f"Mapped {row[0]} to {term_code} / {term_name}")
            else:
                # Impossible to resolve, mark for manual mapping
                log.warning(f"Manual mapping necessary for {row[0]}, domain {domain}")
                manual_mapping_necessary.append(row[0])
        else:
            # Impossible to resolve, mark for manual mapping
            log.warning(f"Manual mapping necessary for {row[0]}")
            manual_mapping_necessary.append(row[0])
    return test_code_mapping, test_name_mapping, manual_mapping_necessary


def create_cttermcontext_for_activity_item_terms(
    db_driver, log, test_code_mapping, test_name_mapping, manual_mapping_necessary
):
    """
    Create CTTermContext for terms in multiple codelists.
    This looks up all terms that are in multiple codelists and targeted by an ActivityItem node,
    then disambiguates the codelist based on rules,
    then matches the term and the picked codelist in the sideloaded CT,
    creates a CTTermContext, and refactors the relationship to point to the new context node.
    """

    # Migrate ActivityItem terms excluding test_name/test_code
    log.info(
        "Creating CTTermContext for terms in multiple codelists targeted by ActivityItem"
    )
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel:HAS_CT_TERM]-(them:ActivityItem)<--(:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue)
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl, aicv.name AS item_class
        WITH us, migrate_rel, them, item_class, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        UNWIND codelists AS cl
        WITH us, migrate_rel, cl, item_class,
        CASE item_class
            WHEN "domain" THEN "DOMAIN"
            WHEN "specimen" THEN "SPECTYPE"
            WHEN "unit_dimension" THEN "UNITDIM"
            WHEN "finding_category" THEN "FINDCAT"
            WHEN "finding_subcategory" THEN "FINDSCAT"
            WHEN "location" THEN "LOC"
            WHEN "event_category" THEN "EVNTCAT"
            WHEN "laterality" THEN "LAT"
            ELSE NULL
            END AS target_codelist_subval
        MATCH (new_us:CTTermRoot_sideload)
        MATCH (new_cl:CTCodelistRoot_sideload)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot_sideload)-->(target_cl:CTCodelistAttributesValue_sideload)
        WHERE target_cl.submission_value=target_codelist_subval AND new_us.uid=us.concept_id
        WITH DISTINCT new_us, new_cl, migrate_rel, target_codelist_subval
        CALL {
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
    """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    # Migrate test_name/test_code
    log.info("Creating CTTermContext for terms targeted by test_code activity items")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel:HAS_CT_TERM]-(them:ActivityItem)<--(:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue {name: "test_code"})
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl
        WITH us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        UNWIND codelists AS cl
        WITH us, migrate_rel, cl, $test_code_mapping[us.concept_id] AS target_codelist_subval
        MATCH (new_us:CTTermRoot_sideload)
        MATCH (new_cl:CTCodelistRoot_sideload)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot_sideload)-->(target_cl:CTCodelistAttributesValue_sideload)
        WHERE target_cl.submission_value=target_codelist_subval AND new_us.uid=us.concept_id
        WITH DISTINCT new_us, new_cl, migrate_rel, target_codelist_subval
        CALL {
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
        """,
        params={"test_code_mapping": test_code_mapping},
    )

    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    log.info("Creating CTTermContext for terms targeted by test_name activity items")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel:HAS_CT_TERM]-(them:ActivityItem)<--(:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue {name: "test_name"})
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name <> "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl
        WITH us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        UNWIND codelists AS cl
        WITH us, migrate_rel, cl, $test_name_mapping[us.concept_id] AS target_codelist_subval
        MATCH (new_us:CTTermRoot_sideload)
        MATCH (new_cl:CTCodelistRoot_sideload)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot_sideload)-->(target_cl:CTCodelistAttributesValue_sideload)
        WHERE target_cl.submission_value=target_codelist_subval AND new_us.uid=us.concept_id
        WITH DISTINCT new_us, new_cl, migrate_rel, target_codelist_subval
        CALL {
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
        """,
        params={"test_name_mapping": test_name_mapping},
    )

    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    if manual_mapping_necessary:
        log.info(
            f"Manual disambiguation necessary for {len(manual_mapping_necessary)} term(s)"
        )
        for term in manual_mapping_necessary:
            log.info(f"Term: {term}")

        _, summary = run_cypher_query(
            db_driver,
            """
                UNWIND $terms AS term
                MATCH (us:CTTermRoot {concept_id: term})<-[migrate_rel:HAS_CT_TERM]-(them:ActivityItem)<--(:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue WHERE aicv.name IN ["test_name", "test_code"])
                MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
                WHERE lib.name <> "Sponsor"
                WITH DISTINCT us, migrate_rel, them, cl, aicv.name AS item_class
                WITH us, migrate_rel, them, item_class, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
                WHERE number_codelists > 1
                WITH DISTINCT us, codelists, collect(migrate_rel) AS migrate_rels
                CALL {
                    WITH us, codelists, migrate_rels
                    CREATE (ctx_new:CTTermContext:MigrateManually)
                    WITH us, codelists, migrate_rels, ctx_new
                    MATCH (new_us:CTTermRoot_sideload) WHERE new_us.uid=us.concept_id
                    CREATE (ctx_new)-[:HAS_SELECTED_TERM]->(new_us)
                    WITH codelists, migrate_rels, ctx_new
                    UNWIND codelists AS cl
                    MATCH (new_cl:CTCodelistRoot_sideload) WHERE cl.uid=new_cl.uid
                    CREATE (ctx_new)-[:HAS_SELECTED_CODELIST]->(new_cl)
                    WITH cl, ctx_new, migrate_rels
                    UNWIND migrate_rels AS migrate_rel
                    WITH ctx_new, migrate_rel
                    CALL apoc.refactor.to(migrate_rel, ctx_new)
                    YIELD output
                    RETURN output AS migrated_rel
                } IN TRANSACTIONS OF 1000 ROWS
                RETURN count(DISTINCT migrated_rel)
            """,
            params={"terms": manual_mapping_necessary},
        )
        print_counters_table(summary.counters)
        contains_updates = contains_updates or summary.counters.contains_updates

    return contains_updates


def create_cttermcontext_for_single_codelist_terms_sponsor(db_driver, log):
    """
    Create CTTermContext for Sponsor terms in a single codelist.
    This looks up all Sponsor terms that are in a single codelist and targeted by a non-CT node,
    then matches the same term and its codelist in the sideloaded CT,
    creates a CTTermContext, and refactors the relationship to point to the new context node.
    """

    log.info("Creating CTTermContext for Sponsor terms in a single codelist")
    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (us:CTTermRoot)<-[migrate_rel]-(them:{NON_CT_LABELS_SELECTION}&!CTCodelistTerm_sideload)
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name = "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl
        WITH us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists = 1
        UNWIND codelists AS cl
        MATCH (new_cl:CTCodelistRoot_sideload)
        WHERE new_cl.uid=cl.uid
        WITH us AS new_us, new_cl, migrate_rel
        CALL {{
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        }} IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
    """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def create_cttermcontext_for_multiple_codelist_terms_sponsor(db_driver, log):
    """
    Create CTTermContext for Sponsor terms in multiple codelists.
    This looks up all Sponsor terms that are in multiple codelists and targeted by a non-CT node,
    then disambiguates the codelist based on rules,
    then matches the term and the picked codelist in the sideloaded CT,
    creates a CTTermContext, and refactors the relationship to point to the new context node.
    """

    log.info("Creating CTTermContext for Sponsor terms in multiple codelists")
    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (us:CTTermRoot)<-[migrate_rel]-(them:{NON_CT_LABELS_SELECTION}&!CTCodelistTerm_sideload&!CTTermContext)
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name = "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl
        WITH us, migrate_rel, them, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        UNWIND codelists AS cl
        WITH us, migrate_rel, cl,
        CASE type(migrate_rel)
            WHEN "HAS_CT_DIMENSION" THEN "Unit Dimension"
            WHEN "HAS_DATA_DOMAIN", "HAS_SDTM_DOMAIN" THEN "SDTM Domain Abbreviation"
            WHEN "HAS_CT_UNIT" THEN "Unit"
            WHEN "HAS_REASON_FOR_NULL_VALUE" THEN "Null Flavor Reason"
            WHEN "HAS_EPOCH_SUB_TYPE" THEN "Epoch Sub Type"
            WHEN "HAS_EPOCH_TYPE" THEN "Epoch Type"
            WHEN "HAS_EPOCH" THEN "Epoch"
            WHEN "HAS_DOSAGE_FORM" THEN "Pharmaceutical Dosage Form"
            WHEN "HAS_ROUTE_OF_ADMINISTRATION" THEN "Route of Administration"
            WHEN "HAS_CONFIGURED_TERM" THEN "Trial Summary Parameter Test Code"
            WHEN "HAS_OBJECTIVE_LEVEL" THEN "Objective Level"
            WHEN "HAS_ENDPOINT_LEVEL" THEN "Endpoint Level"
            WHEN "HAS_TYPE" THEN "Criteria Type"
            WHEN "HAS_CATEGORY" THEN "Objective Category"
            WHEN "HAS_DOSE_FREQUENCY" THEN "Frequency"
            WHEN "HAS_UNIT_SUBSET" THEN "Unit Subset"
            ELSE NULL
            END AS target_codelist_name
        MATCH (new_cl:CTCodelistRoot_sideload)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot_sideload)-->(target_cl:CTCodelistNameValue_sideload)
        WHERE target_cl.name=target_codelist_name
        WITH DISTINCT us AS new_us, new_cl, migrate_rel, target_codelist_name
        CALL {{
           WITH new_us, new_cl, migrate_rel
           MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
           WITH ctx_new, new_us, new_cl, migrate_rel
           CALL apoc.refactor.to(migrate_rel, ctx_new)
           YIELD output
           RETURN output AS migrated_rel
        }} IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def create_cttermcontext_for_activity_item_terms_sponsor(db_driver, log):
    """
    Create CTTermContext for sponsor terms in multiple codelists.
    This looks up all terms that are in multiple codelists and targeted by an ActivityItem node,
    then disambiguates the codelist based on rules,
    then matches the term and the picked codelist in the sideloaded CT,
    creates a CTTermContext, and refactors the relationship to point to the new context node.
    """
    log.info(
        "Creating CTTermContext for sponsor terms in multiple codelists targeted by ActivityItem"
    )
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel:HAS_CT_TERM]-(them:ActivityItem)<--(:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue)
        MATCH (cl:CTCodelistRoot)-[:HAS_TERM]->(us)<-[:CONTAINS_TERM]-(lib:Library)
        WHERE lib.name = "Sponsor"
        WITH DISTINCT us, migrate_rel, them, cl, aicv.name AS item_class
        WITH us, migrate_rel, them, item_class, collect(cl) AS codelists, count(DISTINCT cl) AS number_codelists
        WHERE number_codelists > 1
        UNWIND codelists AS cl
        WITH us, migrate_rel, cl, item_class,
        CASE item_class
            WHEN "domain" THEN "DOMAIN"
            WHEN "specimen" THEN "SPECTYPE"
            WHEN "unit_dimension" THEN "UNITDIM"
            WHEN "finding_category" THEN "FINDCAT"
            WHEN "finding_subcategory" THEN "FINDSCAT"
            WHEN "location" THEN "LOC"
            WHEN "event_category" THEN "EVNTCAT"
            WHEN "laterality" THEN "LAT"
            ELSE NULL
            END AS target_codelist_subval

        MATCH (new_cl:CTCodelistRoot_sideload)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot_sideload)-->(target_cl:CTCodelistAttributesValue_sideload)
        WHERE target_cl.submission_value=target_codelist_subval
        WITH DISTINCT us AS new_us, new_cl, migrate_rel, target_codelist_subval
        CALL {
            WITH new_us, new_cl, migrate_rel
            MERGE (new_cl)<-[:HAS_SELECTED_CODELIST]-(ctx_new:CTTermContext)-[:HAS_SELECTED_TERM]->(new_us)
            WITH ctx_new, new_us, new_cl, migrate_rel
            CALL apoc.refactor.to(migrate_rel, ctx_new)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel)
    """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def migrate_ct_uid_properties(db_driver, log):
    """
    Migrate node properties containing CT term UIDs to the new model.
    This contains StudyFields
    """
    log.info("Migrating nodes with CT term UIDs properties")

    # Standard StudyTextField is connected to CTTerms, in addition to having the value property
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (stf:StudyTextField)-[:HAS_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(t:CTTermRoot_sideload)
        SET stf.value = t.uid
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    # Some StudyTextField are not connected to CTTerms
    # This is the case for null_value_codes
    # Then, just take C48660 out of C48660_NA
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (stf:StudyTextField)
        WHERE NOT EXISTS((stf)-[:HAS_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot_sideload)) AND stf.value=~'C[0-9]{4,6}_.*'
        SET stf.value = split(stf.value, '_')[0]
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    # StudyArrayField can have an array of CTTerms
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (stf:StudyArrayField)-[:HAS_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(t:CTTermRoot_sideload)
        WITH stf, collect(t.uid) AS new_value
        SET stf.value = new_value
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return summary.counters.contains_updates


def migrate_term_to_term_relationships(db_driver, log):
    """
    Migrate term-to-term relationships to the new model.
    This looks up all term-to-term relationships and migrates them to the new model.
    It includes the following relationships:
    - HAS_PARENT_TYPE
    - HAS_PARENT_SUB_TYPE
    - HAS_PREDECESSOR
    """

    # Note that here, summary will not contain stats
    # As write operations are done using APOC refactor procedures
    log.info("Migrating term-to-term relationships")
    result, _ = run_cypher_query(
        db_driver,
        """
        MATCH (source:CTTermRoot)-[migrate_rel:HAS_PARENT_TYPE|HAS_PARENT_SUB_TYPE|HAS_PREDECESSOR]->(:CTTermRoot)
        MATCH (new_source:CTTermRoot_sideload)
        WHERE new_source.uid IN [source.uid, source.concept_id]
        CALL {
            WITH new_source, migrate_rel
            CALL apoc.refactor.from(migrate_rel, new_source)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel) AS count
        """,
    )
    created_rels = result[0]["count"]
    contains_updates = created_rels > 0
    print_counters_table(SummaryCounters({"relationships-created": created_rels}))

    result, _ = run_cypher_query(
        db_driver,
        """
        MATCH (:CTTermRoot_sideload)-[migrate_rel:HAS_PARENT_TYPE|HAS_PARENT_SUB_TYPE|HAS_PREDECESSOR]->(target:CTTermRoot)
        MATCH (new_target:CTTermRoot_sideload)
        WHERE new_target.uid IN [target.uid, target.concept_id]
        CALL {
            WITH new_target, migrate_rel
            CALL apoc.refactor.to(migrate_rel, new_target)
            YIELD output
            RETURN output AS migrated_rel
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(DISTINCT migrated_rel) AS count
        """,
    )
    created_rels = result[0]["count"]
    this_contains_updates = created_rels > 0
    print_counters_table(SummaryCounters({"relationships-created": created_rels}))
    contains_updates = contains_updates or this_contains_updates

    return contains_updates


def migrate_uses_value(db_driver, log):
    """
    Migrate the USES_VALUE relationships between syntax instances and CTTermNameRoot nodes.

    """

    log.info(
        "Creating USES_VALUE relationships between syntax instances and CTTermNameRoot nodes"
    )

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (syntax)-[migrate_rel:USES_VALUE]->(old_term_name_root:CTTermNameRoot)<-[:HAS_NAME_ROOT]-(old_term_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(old_term_attr_val:CTTermAttributesValue)
        WHERE (old_term_root)<-[:CONTAINS_TERM]-(:Library {name: "CDISC"})
        WITH syntax, migrate_rel, old_term_name_root, old_term_root, old_term_attr_val
        MATCH (new_term_name_root:CTTermNameRoot_sideload)<-[:HAS_NAME_ROOT]-(new_term_root:CTTermRoot_sideload)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot_sideload)-[:LATEST]->(new_term_attr_val:CTTermAttributesValue_sideload {concept_id: old_term_attr_val.concept_id})
        MERGE (syntax)-[uv:USES_VALUE {index: migrate_rel.index, position: migrate_rel.position}]->(new_term_name_root)
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates
    return contains_updates


def mark_cdisc_template_parameter_terms(db_driver, log):
    """
    Add the TemplateParameterTermRoot and TemplateParameterTermValue labels to CDISC terms
    that are included in sponsor codelists marked as template parameters.
    Also link the term name root nodes to the codelist name value node with
    HAS_PARAMETER_TERM relationships.
    """

    log.info("Marking CDISC Template Parameter terms")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (cl_name_val:CTCodelistNameValue_sideload&TemplateParameter)<-[:LATEST]-(cl_name_root:CTCodelistNameRoot_sideload)<--(cl:CTCodelistRoot_sideload)-[:HAS_TERM]->(:CTCodelistTerm_sideload)-[:HAS_TERM_ROOT]->(term_root:CTTermRoot_sideload)<-[:CONTAINS_TERM]-(:Library {name: "CDISC"})
        MATCH (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot_sideload)
        MERGE (cl_name_val)-[:HAS_PARAMETER_TERM]->(term_name_root)
        WITH term_name_root, term_root
        CALL {
            WITH term_name_root, term_root
            MATCH (term_name_root)-[:HAS_VERSION]->(term_name_val:CTTermNameValue_sideload)
            SET term_name_root.uid = "TemplateParameterValue_" + term_root.uid
            SET term_name_val:TemplateParameterTermValue
            SET term_name_root:TemplateParameterTermRoot
        }
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    return contains_updates


def mark_cdisc_template_parameter_codelists(db_driver, log):
    """
    Add the TemplateParameter label to the latest name value node of CDISC codelists
    that are intended to be marked as template parameters.
    Also add the TemplateParameterTermRoot and TemplateParameterTermValue labels
    to the included terms.
    Finally link the term name root nodes to the codelist name value node with
    HAS_PARAMETER_TERM relationships.
    """

    log.info("Marking CDISC Template Parameter codelists and their terms")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (old_tp:CTCodelistNameValue&TemplateParameter)<-[:LATEST]-(:CTCodelistNameRoot)<--(old_cl_root:CTCodelistRoot)<-[:CONTAINS_CODELIST]-(:Library {name: "CDISC"})
        WITH old_cl_root.uid AS cl_uid, old_tp
        CALL {
            WITH cl_uid, old_tp
            MATCH (cl_name_val:CTCodelistNameValue_sideload)<-[:LATEST]-(cl_name_root:CTCodelistNameRoot_sideload)<--(cl_root:CTCodelistRoot_sideload {uid: cl_uid})
            SET cl_name_val:TemplateParameter
            WITH cl_name_val, cl_name_root, cl_root, old_tp
            CALL {
                WITH cl_name_val, old_tp
                MATCH (old_tp)<-[old_up:USES_PARAMETER]-(syntax)
                MERGE (syntax)-[new_up:USES_PARAMETER {position: old_up.position}]->(cl_name_val)
            }
            WITH cl_name_val, cl_name_root, cl_root, old_tp
            CALL {
                WITH cl_name_val, cl_name_root, cl_root
                MATCH (cl_root)-[:HAS_TERM]->(:CTCodelistTerm_sideload)-[:HAS_TERM_ROOT]->(term_root:CTTermRoot_sideload)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot_sideload)
                MERGE (cl_name_val)-[:HAS_PARAMETER_TERM]->(term_name_root)
                WITH term_name_root, term_root
                CALL {
                    WITH term_name_root, term_root
                    MATCH (term_name_root)-[:HAS_VERSION]->(term_name_val:CTTermNameValue_sideload)
                    SET term_name_root.uid = "TemplateParameterValue_" + term_root.uid
                    SET term_name_val:TemplateParameterTermValue
                    SET term_name_root:TemplateParameterTermRoot
                }
            }
        }
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    return contains_updates


def migrate_sponsor_ct_packages(db_driver, log):
    """
    Migrate sponsor CT packages by linking them to the updated standard CT packages.
    """

    log.info("Migrating sponsor CT packages")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (sponsor_pkg:CTPackage)-[:EXTENDS_PACKAGE]->(old_standard_pkg:CTPackage)
        MATCH (new_standard_pkg:CTPackage_sideload)<-[:CONTAINS_PACKAGE]-(new_catalogue) WHERE toLower(new_standard_pkg.name)=toLower(old_standard_pkg.name)
        MERGE (sponsor_pkg)-[:EXTENDS_PACKAGE]->(new_standard_pkg)
        MERGE (new_catalogue)-[:CONTAINS_PACKAGE]->(sponsor_pkg)
        WITH sponsor_pkg
        SET sponsor_pkg.effective_date = dateTime(sponsor_pkg.effective_date)
        WITH sponsor_pkg
        CALL apoc.create.setLabels(sponsor_pkg, ['CTPackage_sideload']) YIELD node
        RETURN node
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    return contains_updates


def remove_old_ct_and_relabel_nodes(db_driver, log):
    """
    Remove old CT elements, and relabel the sideloaded ones
    so they match the target model.
    """

    log.info("Removing old CT elements and relabeling sideloaded ones")

    # Remove CT elements that are not double-labeled (CDISC ones)
    _, summary = run_cypher_query(
        db_driver,
        """
        WITH 
            ["CTCatalogue_sideload", "CTPackage_sideload", "CTCodelistRoot_sideload", "CTCodelistNameRoot_sideload", "CTCodelistAttributesRoot_sideload", "CTPackageCodelist_sideload", "CTCodelistAttributesValue_sideload", "CTCodelistNameValue_sideload", "CTTermRoot_sideload", "CTTermNameRoot_sideload", "CTTermAttributesRoot_sideload", "CTPackageTerm_sideload", "CTCodelistTerm_sideload", "CTTermAttributesValue_sideload", "CTTermNameValue_sideload"] AS new_labels,
            ["CTCatalogue", "CTPackage", "CTCodelistRoot", "CTCodelistNameRoot", "CTCodelistAttributesRoot", "CTPackageCodelist", "CTCodelistAttributesValue", "CTCodelistNameValue", "CTTermRoot", "CTTermNameRoot", "CTTermAttributesRoot", "CTPackageTerm", "CTTermAttributesValue", "CTTermNameValue"] AS old_labels
        MATCH (old_only) WHERE none(label IN labels(old_only) WHERE label IN new_labels) AND any(label IN labels(old_only) WHERE label IN old_labels)
        CALL {
            WITH old_only
            DETACH DELETE old_only
        } IN TRANSACTIONS OF 1000 ROWS
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    # Relabel mixed elements (sponsor) so they only have the sideload label
    _, summary = run_cypher_query(
        db_driver,
        """
        WITH 
            ["CTCatalogue_sideload", "CTPackage_sideload", "CTCodelistRoot_sideload", "CTCodelistNameRoot_sideload", "CTCodelistAttributesRoot_sideload", "CTPackageCodelist_sideload", "CTCodelistAttributesValue_sideload", "CTCodelistNameValue_sideload", "CTTermRoot_sideload", "CTTermNameRoot_sideload", "CTTermAttributesRoot_sideload", "CTPackageTerm_sideload", "CTCodelistTerm_sideload", "CTTermAttributesValue_sideload", "CTTermNameValue_sideload"] AS new_labels,
            ["CTCatalogue", "CTPackage", "CTCodelistRoot", "CTCodelistNameRoot", "CTCodelistAttributesRoot", "CTPackageCodelist", "CTCodelistAttributesValue", "CTCodelistNameValue", "CTTermRoot", "CTTermNameRoot", "CTTermAttributesRoot", "CTPackageTerm", "CTTermAttributesValue", "CTTermNameValue"] AS old_labels
        MATCH (mixed) WHERE any(label IN labels(mixed) WHERE label IN new_labels) AND any(label IN labels(mixed) WHERE label IN old_labels)
        CALL {
            WITH mixed
            REMOVE mixed:CTCatalogue
            REMOVE mixed:CTPackage
            REMOVE mixed:CTCodelistRoot
            REMOVE mixed:CTCodelistNameRoot
            REMOVE mixed:CTCodelistAttributesRoot
            REMOVE mixed:CTPackageCodelist
            REMOVE mixed:CTCodelistAttributesValue
            REMOVE mixed:CTCodelistNameValue
            REMOVE mixed:CTTermRoot
            REMOVE mixed:CTTermNameRoot
            REMOVE mixed:CTTermAttributesRoot
            REMOVE mixed:CTPackageTerm
            REMOVE mixed:CTTermAttributesValue
            REMOVE mixed:CTTermNameValue
        } IN TRANSACTIONS OF 1000 ROWS
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    # Relabel from sideload to target model
    _, summary = run_cypher_query(
        db_driver,
        """
        WITH 
            ["CTCatalogue_sideload", "CTPackage_sideload", "CTCodelistRoot_sideload", "CTCodelistNameRoot_sideload", "CTCodelistAttributesRoot_sideload", "CTPackageCodelist_sideload", "CTCodelistAttributesValue_sideload", "CTCodelistNameValue_sideload", "CTTermRoot_sideload", "CTTermNameRoot_sideload", "CTTermAttributesRoot_sideload", "CTPackageTerm_sideload", "CTCodelistTerm_sideload", "CTTermAttributesValue_sideload", "CTTermNameValue_sideload"] AS new_labels,
            ["CTCatalogue", "CTPackage", "CTCodelistRoot", "CTCodelistNameRoot", "CTCodelistAttributesRoot", "CTPackageCodelist", "CTCodelistAttributesValue", "CTCodelistNameValue", "CTTermRoot", "CTTermNameRoot", "CTTermAttributesRoot", "CTPackageTerm", "CTTermAttributesValue", "CTTermNameValue"] AS old_labels
        MATCH (new_only) WHERE any(label IN labels(new_only) WHERE label IN new_labels) AND none(label IN labels(new_only) WHERE label IN old_labels)
        WITH new_only, [label IN labels(new_only) WHERE label CONTAINS "_sideload"][0] AS migrate_label
        WITH new_only, migrate_label, replace(migrate_label, "_sideload", "") AS new_label
        CALL {
            WITH  new_only, migrate_label
            CALL apoc.create.removeLabels( new_only, [ migrate_label ] )
            YIELD node
        } IN TRANSACTIONS OF 1000 ROWS
        CALL {
            WITH new_only, new_label
            CALL apoc.create.addLabels( new_only, [ new_label ] )
            YIELD node
        } IN TRANSACTIONS OF 1000 ROWS
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return contains_updates


def migrate_cdisc_epoch_terms(db_driver, log):
    """
    Migrate the updated CDISC Epoch terms.
    - Intervention: replace the old sponsor defined term with the new CDISC term C209541
    - Screening: replace the old term C48262 with the new C202487
    """

    log.info("Migrating updated CDISC Epoch terms")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (epoch_subtype_cl:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(:CTCodelistNameValue {name: "Epoch Sub Type"})
        MATCH (epochcl:CTCodelistRoot {uid: "C99079"})-[cht:HAS_TERM]-(cclt:CTCodelistTerm {submission_value:"INTERVENTION"})-[chtr:HAS_TERM_ROOT]-(ctr:CTTermRoot)-[:CONTAINS_TERM]-(:Library {name:"CDISC"})
        WHERE NOT (cclt)-[:HAS_TERM]-(epoch_subtype_cl)
        MATCH (epochcl)-[sht:HAS_TERM]-(sclt:CTCodelistTerm {submission_value:"INTERVENTION"})-[shtr:HAS_TERM_ROOT]-(str:CTTermRoot)-[:CONTAINS_TERM]-(:Library {name:"Sponsor"})
        WHERE sht.end_date IS NULL

        // End the sponsor defined term in Epoch codelist
        CALL {
            WITH cht, sht
            SET sht.end_date = cht.start_date
        }
        // End the sponsor term and add the CDISC term to the Epoch subtype codelist
        CALL {
            WITH cclt, sclt, cht, epoch_subtype_cl
            MATCH (epoch_subtype_cl)-[stht:HAS_TERM]->(sclt)
            SET stht.end_date = cht.start_date
            MERGE (epoch_subtype_cl)-[ht:HAS_TERM]->(cclt)
            SET ht += properties(cht)
        }
        // Set intervention term as its own parent sub type
        CALL {
            WITH ctr
            MERGE (ctr)-[:HAS_PARENT_SUB_TYPE]->(ctr)
        }
        // Copy parent sub types from the sponsor defined term to the CDISC defined term
        CALL {
            WITH str, ctr
            MATCH (str)<-[hpst:HAS_PARENT_SUB_TYPE]-(pst) WHERE pst <> str
            MERGE (ctr)<-[:HAS_PARENT_SUB_TYPE]-(pst)
            DELETE hpst
        }
        // Copy parent types from the sponsor defined term to the CDISC defined term
        CALL {
            WITH str, ctr
            MATCH (str)-[hpst:HAS_PARENT_TYPE]->(pt) WHERE pt <> str
            MERGE (ctr)-[:HAS_PARENT_TYPE]->(pt)
            DELETE hpst
        }
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    # Migrate from the old to the new CDISC Screening term
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (epoch_subtype_cl:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(:CTCodelistNameValue {name: "Epoch Sub Type"})
        MATCH (epoch_subtype_cl)-[old_st_ht:HAS_TERM]-(:CTCodelistTerm)-[:HAS_TERM_ROOT]-(old_st_tr:CTTermRoot {uid: "C48262"})
        WHERE old_st_ht.end_date IS NULL
        MATCH (epoch_cl:CTCodelistRoot {uid: "C99079"})-[new_epoch_ht:HAS_TERM]-(new_epoch_clt:CTCodelistTerm)-[new_epoch_htr:HAS_TERM_ROOT]-(new_epoch_tr:CTTermRoot {uid: "C202487"})

        // End the old term and add the new term to the Epoch Sub Type codelist
        CALL {
            WITH new_epoch_clt, old_st_ht, epoch_subtype_cl, new_epoch_ht
            SET old_st_ht.end_date = new_epoch_ht.start_date
            MERGE (epoch_subtype_cl)-[ht:HAS_TERM]->(new_epoch_clt)
            SET ht += properties(new_epoch_ht)
        }
        // Set the new term as its own parent sub type
        CALL {
            WITH new_epoch_tr
            MERGE (new_epoch_tr)-[:HAS_PARENT_SUB_TYPE]->(new_epoch_tr)
        }
        // Copy parent sub types from the old term to the new term
        CALL {
            WITH old_st_tr, new_epoch_tr
            MATCH (old_st_tr)<-[hpst:HAS_PARENT_SUB_TYPE]-(pst) WHERE pst <> old_st_tr
            MERGE (new_epoch_tr)<-[:HAS_PARENT_SUB_TYPE]-(pst)
            DELETE hpst
        }
        // Copy parent types from the old term to the new term
        CALL {
            WITH old_st_tr, new_epoch_tr
            MATCH (old_st_tr)-[hpst:HAS_PARENT_TYPE]->(pt) WHERE pt <> old_st_tr
            MERGE (new_epoch_tr)-[:HAS_PARENT_TYPE]->(pt)
            DELETE hpst
        }
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return contains_updates


def cleanup(db_driver, log):
    """
    Cleanup the database by removing any leftover relationships or properties.
    This includes :
    * HAS_TERM between CTCodelistRoot and CTTermRoot
    * code_submission_value on :CTTermAttributesValue
    """

    log.info("Cleaning up the database - Removing HAS_TERM relationships")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (cl:CTCodelistRoot)-[ht:HAS_TERM]->(us:CTTermRoot)
        WHERE EXISTS((cl)-->(:CTCodelistTerm)-->(us))
        CALL {
            WITH ht
            DELETE ht
        } IN TRANSACTIONS OF 1000 ROWS
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    log.info("Cleaning up the database - Removing code_submission_value property")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:CTTermAttributesValue) REMOVE n.code_submission_value 
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return contains_updates


if __name__ == "__main__":
    main()
