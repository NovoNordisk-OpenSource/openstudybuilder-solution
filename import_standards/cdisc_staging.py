import os
import json
import datetime
import json
import logging
from copy import deepcopy
import openpyxl
import re
import time
from os import environ
import argparse

import neo4j
from neo4j import GraphDatabase


NEO4J_HOST = environ.get("NEO4J_CDISC_IMPORT_HOST")
NEO4J_BOLT_PORT = environ.get("NEO4J_CDISC_IMPORT_BOLT_PORT")
NEO4J_AUTH_USER = environ.get("NEO4J_CDISC_IMPORT_AUTH_USER")
NEO4J_AUTH_PASSWORD = environ.get("NEO4J_CDISC_IMPORT_AUTH_PASSWORD")
NEO4J_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE")
NEO4J_PROTOCOL = environ.get("NEO4J_PROTOCOL", "neo4j")
CDISC_JSON_DIR = environ.get("CDISC_JSON_DIR")
CDISC_XLS_DIR = environ.get("CDISC_XLS_DIR")

# Check if all required environment variables are set
if not NEO4J_HOST:
    raise ValueError("NEO4J_CDISC_IMPORT_HOST environment variable is not set")
if not NEO4J_BOLT_PORT:
    raise ValueError("NEO4J_CDISC_IMPORT_BOLT_PORT environment variable is not set")
if not NEO4J_AUTH_USER:
    raise ValueError("NEO4J_CDISC_IMPORT_AUTH_USER environment variable is not set")
if not NEO4J_AUTH_PASSWORD:
    raise ValueError("NEO4J_CDISC_IMPORT_AUTH_PASSWORD environment variable is not set")
if not NEO4J_DATABASE:
    raise ValueError("NEO4J_CDISC_IMPORT_DATABASE environment variable is not set")
if not CDISC_JSON_DIR:
    raise ValueError("CDISC_JSON_DIR environment variable is not set")
if not CDISC_XLS_DIR:
    raise ValueError("CDISC_XLS_DIR environment variable is not set")

# Batch sizes for processing
TERM_BATCH_SIZE = 1000
CODELIST_BATCH_SIZE = 100


def get_logger():
    loglevel = environ.get("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {loglevel}, defaulting to INFO")
        numeric_level = logging.INFO
    logging.basicConfig()
    logger = logging.getLogger("CDISC staging")
    logger.setLevel(numeric_level)
    return logger

LOGGER = get_logger()


# Database connection and query functions
def get_neo4j_driver(database=None):
    uri = "{}://{}:{}".format(NEO4J_PROTOCOL, NEO4J_HOST, NEO4J_BOLT_PORT)
    return GraphDatabase.driver(
        uri,
        auth=(NEO4J_AUTH_USER, NEO4J_AUTH_PASSWORD),
        database=database,
        max_connection_lifetime=1800,
        keep_alive=True,
        connection_acquisition_timeout=60.0,
        liveness_check_timeout=30.0,
    )


def run_query(tx, query, parameters=None):
    return tx.run(query, parameters)


def run_single_query(session, query, parameters=None):
    with session.begin_transaction() as tx:
        data = tx.run(query, parameters).data()
        return data

def create_database(db_driver, db_name, clear_db=False):
    try:
        with db_driver.session() as session:
            query = f"CREATE DATABASE `{db_name}` IF NOT EXISTS"
            run_single_query(session, query)
    except neo4j.exceptions.Neo4jError:
        LOGGER.info(f"Could not execute query for creating database '{db_name}', normal if running against an AuraDB instance")
    try_cnt = 1
    db_exists = False
    while try_cnt < 10 and not db_exists:
        try:
            with db_driver.session(database=db_name) as session:
                run_single_query(session, "MATCH (n) RETURN n LIMIT 1", parameters=None)
            db_exists = True
        except (
            neo4j.exceptions.ClientError,
            neo4j.exceptions.DatabaseUnavailable,
            neo4j.exceptions.ServiceUnavailable,
        ) as exc:
            LOGGER.info(
                f"Database {db_name} still not reachable, {exc}, pausing for one second"
            )
            try_cnt += 1
            time.sleep(1)
    if not db_exists:
        raise RuntimeError(f"db {db_name} is not available")
    if clear_db:
        LOGGER.info(f"Clearing the '{NEO4J_DATABASE}' database")
        with db_driver.session(database=db_name) as session:
            session.run("""
                MATCH (n)
                CALL (n) {
                    DETACH DELETE n
                } IN TRANSACTIONS OF 5000 ROWS
                """, None)

# Create indexes to increase performace
def create_indexes(session):
    queries = [
        "CREATE INDEX raw_package_date IF NOT EXISTS FOR (n:RawPackage) ON (n.effectiveDate)",
        "CREATE INDEX raw_catalogue_date IF NOT EXISTS FOR (n:RawCatalogue) ON (n.effectiveDate)",
        "CREATE INDEX raw_codelist_cid IF NOT EXISTS FOR (n:RawCodelist) ON (n.conceptId)",
        "CREATE INDEX raw_term_cid IF NOT EXISTS FOR (n:RawTerm) ON (n.conceptId)",
        "CREATE INDEX gr_codelist_cid IF NOT EXISTS FOR (n:GroupedCodelist) ON (n.conceptId)",
        "CREATE INDEX gr_term_cid IF NOT EXISTS FOR (n:GroupedTerm) ON (n.conceptId)",
        "CREATE INDEX ver_codelist_cid IF NOT EXISTS FOR (n:VersionedCodelist) ON (n.conceptId)",
        "CREATE INDEX ver_term_cid IF NOT EXISTS FOR (n:VersionedTerm) ON (n.conceptId)",
    ]
    for query in queries:
        run_single_query(session, query)


###################################################
## Step 1: Load the raw JSON data into the database
###################################################


# Flatten the links object in the data to avoid nested objects
def flatten_links(data):
    flat_links = {}
    links = data.pop("_links")
    for ref, link in links.items():
        for key, val in link.items():
            flat_key = f"_links.{ref}.{key}"
            flat_links[flat_key] = val
    data.update(flat_links)


def merge_package(session, data):
    query = """
        MERGE (p:RawPackage {effectiveDate: $props.effectiveDate})
        MERGE (p)-[:HAS_RAW_CATALOGUE]->(cat:RawCatalogue {name: $props.name})
        SET cat += $props
        WITH cat
        MATCH (prevcat:RawCatalogue {`_links.self.href`: $props.`_links.priorVersion.href`})
        MERGE (cat)-[:HAS_PRIOR_VERSION]->(prevcat)
        RETURN cat
        """
    run_single_query(session, query, parameters={"props": data})


def merge_codelist(session, data, package_catalogue_name):
    query = """
            MATCH (cat:RawCatalogue {name: $package_catalogue_name})
            OPTIONAL MATCH (cat)-[:HAS_PRIOR_VERSION]->(prevcat:RawCatalogue)
            MERGE (cat)-[:HAS_RAW_CODELIST]->(cl:RawCodelist {conceptId: $props.conceptId})
            SET cl += $props
            WITH cl, cat, prevcat
            MATCH (prevcat)-[:HAS_RAW_CODELIST]->(prevcl:RawCodelist {conceptId: $props.conceptId})
            MERGE (cl)-[:HAS_PRIOR_VERSION]->(prevcl)
            RETURN cl
            """
    run_single_query(
        session,
        query,
        parameters={"props": data, "package_catalogue_name": package_catalogue_name},
    )


def merge_terms(session, terms, package_catalogue_name, codelist_id):
    query = """
            MATCH (cat:RawCatalogue {name: $package_catalogue_name})-[:HAS_RAW_CODELIST]->(cl:RawCodelist {conceptId: $codelist_id})
            FOREACH (term in $terms |
                MERGE (cl)-[:HAS_RAW_TERM]->(t:RawTerm {conceptId: term.conceptId})
                SET t += term
            )
            """
    run_single_query(
        session,
        query,
        parameters={
            "terms": terms,
            "package_catalogue_name": package_catalogue_name,
            "codelist_id": codelist_id,
        },
    )


def process_codelist(session, data, package_catalogue_name):
    terms = data.pop("terms")
    merge_codelist(session, data, package_catalogue_name)
    codelist_id = data["conceptId"]
    merge_terms(session, terms, package_catalogue_name, codelist_id)


def process_package_file(session, data):
    flatten_links(data)
    codelists = data.pop("codelists")
    # Uppercase the package name as this is not quite consistent between dates
    data["name"] = data["name"].upper()
    package_catalogue_name = data["name"]
    merge_package(session, data)
    for codelist in codelists:
        process_codelist(session, codelist, package_catalogue_name)


def process_package(session, date, json_files):

    package_ending = date + ".json"
    included_json_files = [f for f in json_files if package_ending in f]
    LOGGER.info("Processing date %s: %s", date, ", ".join(included_json_files))
    for file in included_json_files:
        LOGGER.debug(file)
        with open(os.path.join(CDISC_JSON_DIR, file), "r") as f:
            data = json.load(f)
            process_package_file(session, data)


def process_all_packages(db_driver):
    # Get a list of files in the "CDISC_JSON_DIR" directory
    json_files = os.listdir(CDISC_JSON_DIR)
    json_files = [f for f in json_files if f.endswith(".json")]
    LOGGER.info(f"Found {len(json_files)} JSON files in {CDISC_JSON_DIR}")

    dates = set()
    for file in json_files:
        # Extract the date from the filename, example sdtmct_2018-12-21.json
        date = file[-15:-5]
        dates.add(date)
    LOGGER.debug(dates)

    with db_driver.session(database=NEO4J_DATABASE) as session:
        for date in sorted(dates):
            process_package(session, date, json_files)


########################################################
## Step 2: Group terms and codelists based on concept id
########################################################


def strip_unwanted_quotes(string):
    return string.strip('"').replace('""', '"')


def get_package_dates(session):
    query = "MATCH (p:RawPackage) RETURN DISTINCT p.effectiveDate as package_date ORDER BY date(package_date)"
    result = run_single_query(session, query)
    LOGGER.debug("dates: %s", result)
    # return result
    return [record["package_date"] for record in result]


def get_codelist_cids(session, package_date):
    query = "MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(cl:RawCodelist) RETURN DISTINCT cl.conceptId as cid ORDER BY cid"
    result = run_single_query(session, query, parameters={"package_date": package_date})
    return [record["cid"] for record in result]


def get_codelist_properties(session, package_date):
    query = """
    MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(cl:RawCodelist) WITH DISTINCT cl.conceptId as cid ORDER BY cid
    CALL
    {
        WITH cid
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: cid})-[:SOURCE_CODELIST_DEF]->(rc:RawCodelist)-[]-(rcat:RawCatalogue)
        WITH *, [(rc)-[:HAS_RAW_TERM]-(rt:RawTerm) | [rt.conceptId, rt.submissionValue]] AS terms_cid_sumbval
        WITH p, gc, collect(rc) as raw_defs, collect(rcat) as raw_cats, collect(apoc.map.fromPairs(terms_cid_sumbval)) as cl_terms
        RETURN *
    }
    RETURN *
    """
    result = run_single_query(session, query, parameters={"package_date": package_date})
    return result


def get_term_cids(session, package_date, start, nbr):
    query = "MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(:RawCodelist)--(t:RawTerm) RETURN DISTINCT t.conceptId as cid ORDER BY cid SKIP $start LIMIT $nbr"
    result = run_single_query(
        session,
        query,
        parameters={"package_date": package_date, "start": start, "nbr": nbr},
    )
    return [record["cid"] for record in result]


def get_term_properties(session, package_date, start, nbr):
    query = """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(:RawCodelist)--(t:RawTerm) WITH DISTINCT t.conceptId as cid ORDER BY cid SKIP $start LIMIT $nbr
        CALL (cid) {
            MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: cid})-[:SOURCE_TERM_DEF]->(rt:RawTerm)-[]-(:RawCodelist)-[]-(rcat:RawCatalogue)
            RETURN p, gt, collect(rt) as raw_defs, collect(rcat) as raw_cats
        }
        RETURN *
    """
    result = run_single_query(
        session,
        query,
        parameters={"package_date": package_date, "start": start, "nbr": nbr},
    )
    return result


def get_codelist_terms(session, package_date, codelist_cid):
    query = "MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(:RawCodelist {conceptId: $codelist_cid})--(t:RawTerm) RETURN DISTINCT t.conceptId as cid, t.submissionValue as submval ORDER BY cid"
    result = run_single_query(
        session,
        query,
        parameters={"package_date": package_date, "codelist_cid": codelist_cid},
    )
    return result


def create_grouped_codelists(session, package_date, codelists_cids):
    query = """
            MATCH (p:RawPackage {effectiveDate: $package_date})
            UNWIND $codelist_cids as codelist_cid
                MERGE (p)-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist {conceptId: codelist_cid})
                WITH p, gc, codelist_cid
                MATCH (p)-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[:HAS_RAW_CODELIST]->(cl:RawCodelist {conceptId: codelist_cid})
                MERGE (cl)<-[:SOURCE_CODELIST_DEF]-(gc)
            """
    run_single_query(
        session,
        query,
        parameters={"package_date": package_date, "codelist_cids": codelists_cids},
    )


def create_grouped_terms(session, package_date, term_cids):
    query = """
            MATCH (p:RawPackage {effectiveDate: $package_date})
            UNWIND $term_cids as term_cid
                MERGE (p)-[:HAS_GROUPED_TERM]->(gt:GroupedTerm {conceptId: term_cid})
                WITH p, gt, term_cid
                MATCH (p)-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[:HAS_RAW_CODELIST]->(:RawCodelist)-[:HAS_RAW_TERM]->(t:RawTerm {conceptId: term_cid})
                MERGE (t)<-[:SOURCE_TERM_DEF]-(gt)
            """
    run_single_query(
        session,
        query,
        parameters={"package_date": package_date, "term_cids": term_cids},
    )


def add_grouped_codelist_terms(session, package_date, codelist_cid):
    terms = get_codelist_terms(session, package_date, codelist_cid)
    query = """
            MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: $codelist_cid})
            WITH DISTINCT gc, p
            UNWIND $terms as term
                MATCH (p)-[:HAS_GROUPED_TERM]->(gt:GroupedTerm {conceptId: term.cid})
                MERGE (gc)-[ht:HAS_TERM]->(gt)
                ON CREATE SET ht.rawSubmissionValues = [term.submval], ht.submissionValue = term.submval
                // Append term.submval to rawSubmissionValues only if it's not already present (list-based dedupe)
                ON MATCH SET ht.rawSubmissionValues = CASE WHEN term.submval IN ht.rawSubmissionValues THEN ht.rawSubmissionValues ELSE ht.rawSubmissionValues + term.submval END
            """
    run_single_query(
        session,
        query,
        parameters={
            "package_date": package_date,
            "codelist_cid": codelist_cid,
            "terms": terms,
        },
    )


def group_data(db_driver):
    with db_driver.session(database=NEO4J_DATABASE) as session:
        dates = get_package_dates(session)
        for date in dates:
            codelists_cids = get_codelist_cids(session, date)
            create_grouped_codelists(session, date, codelists_cids)
            start = 0
            while True:
                term_cids = get_term_cids(session, date, start, TERM_BATCH_SIZE)
                returned_nbr = len(term_cids)
                LOGGER.info(
                    "Process terms: start: %s, date: %s, nbr: %s",
                    start,
                    date,
                    returned_nbr,
                )
                start += returned_nbr
                create_grouped_terms(session, date, term_cids)
                if returned_nbr < TERM_BATCH_SIZE:
                    break
            for codelist_cid in codelists_cids:
                add_grouped_codelist_terms(session, date, codelist_cid)


## Step 3: Group term and codelist definitions and identify inconsistencies


def extract_codelist_props(raw_props):
    props = {
        "definition": raw_props["definition"],
        "name": raw_props["name"],
        "preferredTerm": raw_props["preferredTerm"],
        "extensible": raw_props.get("extensible"),
        "submissionValue": raw_props.get("submissionValue"),
        "synonyms": raw_props.get("synonyms"),
    }
    return props


def extract_term_props(raw_props):
    props = {
        "definition": raw_props["definition"],
        "preferredTerm": raw_props["preferredTerm"],
        "synonyms": raw_props.get("synonyms"),
    }
    return props


def merge_codelist_properties(session, package_date):

    add_props_query_multi = """
        UNWIND $codelists as props
        MATCH (p:RawPackage {effectiveDate: props.package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: props.codelist_cid})
        MERGE (gc)-[:HAS_GROUPED_PROPERTIES]->(cp:GroupedCodelistProperties)
        SET cp += props.cl_props RETURN cp
        """
    add_inconsistency_query_multi = """
        UNWIND $codelists as props
        MATCH (p:RawPackage {effectiveDate: props.package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: props.codelist_cid})
        MERGE (gc)-[:HAS_INCONSISTENCY]->(ip:InconsistentCodelistProperties {property: props.property, inconsistency: props.details.inconsistency})
        SET ip += props.details RETURN ip
        """
    add_term_inconsistency_query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: $codelist_cid})
        MERGE (gc)-[:HAS_INCONSISTENCY]->(it:InconsistentCodelistTerms {property: "terms", inconsistency: "inconsistent sets of terms"})
        """

    mark_bad_submission_values_query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(cl:GroupedCodelist)-[ht]-(t:GroupedTerm)
        WHERE size(ht.rawSubmissionValues) = 1 AND ht.rawSubmissionValues[0] STARTS WITH '"' and  ht.rawSubmissionValues[0] ENDS WITH '"'
        MERGE (cl)-[:HAS_INCONSISTENCY]->(it:InconsistentCodelistTerms {property: "term_submval", term_cid: t.conceptId, inconsistency: "unwanted quotes"})
    """

    mark_conflicting_submission_values_query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(cl:GroupedCodelist)-[ht]-(t:GroupedTerm)
        WHERE size(ht.rawSubmissionValues) > 1
        MERGE (cl)-[:HAS_INCONSISTENCY]->(it:InconsistentCodelistTerms {property: "term_submval", term_cid: t.conceptId, inconsistency: "conflicting values"})
    """

    codelists_with_props = get_codelist_properties(session, package_date)
    consistent_codelists = []
    inconsistent_codelists = []
    for codelist in codelists_with_props:
        raw_props = codelist["raw_defs"][0]
        props = extract_codelist_props(raw_props)
        consistent = True
        correct = True

        # Quick check if all definitions are the same
        for cl_props in codelist["raw_defs"][1:]:
            if extract_codelist_props(cl_props) != props:
                LOGGER.debug("Different properties")
                consistent = False
                break

        # Check for unwanted quotes in any of the properties
        for prop, val in props.items():
            if prop == "synonyms":
                if val is not None and val[0].startswith('"') and val[-1].endswith('"'):
                    LOGGER.info("Unwanted quotes in %s", prop)
                    correct = False
            else:
                if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
                    LOGGER.info("Unwanted quotes in %s", prop)
                    correct = False

        if consistent and correct:
            LOGGER.debug(
                "All definitions of codelist %s have consistent properties", codelist["cid"]
            )
            consistent_codelists.append({
                    "package_date": package_date,
                    "codelist_cid": codelist["cid"],
                    "cl_props": props,
                })
        elif not consistent:
            details = cl_inconsistency_details(
                codelist["raw_defs"], codelist["raw_cats"]
            )
            for key, val in details.items():
                LOGGER.info("Inconsistency in %s: %s", key, val)
                inconsistent_codelists.append({
                    "package_date": package_date,
                    "codelist_cid": codelist["cid"],
                    "property": key,
                    "details": val,
                })
        elif not correct:
            details = error_details(props)
            for key, val in details.items():
                LOGGER.info("Error in %s: %s", key, val)
                inconsistent_codelists.append({
                    "package_date": package_date,
                    "codelist_cid": codelist["cid"],
                    "property": key,
                    "details": val,
                })

        terms_consistent = True
        cl_terms = codelist["cl_terms"][0]
        # First check if all codelist definitions have the same terms, with the same submission values
        for terms in codelist["cl_terms"][1:]:
            if set(terms.keys()) != set(cl_terms.keys()):
                LOGGER.debug("Different terms")
                terms_consistent = False
                break
            # check submission values, but ignore the unwanted quotes for now
            if set(strip_unwanted_quotes(val) for val in terms.values()) != set(
                strip_unwanted_quotes(val) for val in cl_terms.values()
            ):
                LOGGER.debug("Different submission values")
                terms_consistent = False
                break

        if not terms_consistent:
            LOGGER.info("Codelist definitions have inconsistent terms")
            run_single_query(
                session,
                add_term_inconsistency_query,
                parameters={"package_date": package_date, "codelist_cid": codelist["cid"]},
            )

    run_single_query(
        session,
        add_props_query_multi,
        parameters={"codelists": consistent_codelists},
    )
    run_single_query(
        session,
        add_inconsistency_query_multi,
        parameters={"codelists": inconsistent_codelists},
    )

    # Check for bad submission values with unwanted quotes
    run_single_query(
        session,
        mark_bad_submission_values_query,
        parameters={"package_date": package_date},
    )
    run_single_query(
        session,
        mark_conflicting_submission_values_query,
        parameters={"package_date": package_date},
    )


def merge_term_properties(session, package_date):

    add_props_query_multi = """
        UNWIND $terms as props
        MATCH (p:RawPackage {effectiveDate: props.package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: props.term_cid})
        MERGE (gt)-[:HAS_GROUPED_PROPERTIES]->(tp:GroupedTermProperties)
        SET tp += props.term_props RETURN tp
        """
    add_inconsistency_query_multi = """
        UNWIND $terms as props
        MATCH (p:RawPackage {effectiveDate: props.package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: props.term_cid})
        MERGE (gt)-[:HAS_INCONSISTENCY]->(ip:InconsistentTermProperties {property: props.property, inconsistency: props.details.inconsistency})
        SET ip += props.details RETURN ip
        """
    
    start = 0
    while True:
        terms_with_props = get_term_properties(session, package_date, start, TERM_BATCH_SIZE)
        returned_nbr = len(terms_with_props)
        LOGGER.info(
            "Process terms: start: %s, date: %s, nbr: %s",
            start,
            package_date,
            returned_nbr,
        )

        start += returned_nbr

        consistent_terms = []
        inconsistent_terms = []

        for term in terms_with_props:
            raw_props = term["raw_defs"][0]
            props = extract_term_props(raw_props)
            consistent = True
            correct = True

            # Quick check if all definitions are the same
            for term_props in term["raw_defs"][1:]:
                if extract_term_props(term_props) != props:
                    LOGGER.debug("Different properties")
                    consistent = False
                    break

            # Check for unwanted quotes in any of the properties
            for prop, val in props.items():
                if prop == "synonyms":
                    if (
                        val is not None
                        and val[0].startswith('"')
                        and val[-1].endswith('"')
                    ):
                        LOGGER.info(f"Unwanted quotes in {prop}")
                        correct = False
                else:
                    if val.startswith('"') and val.endswith('"'):
                        LOGGER.info(f"Unwanted quotes in {prop}")
                        correct = False

            if consistent and correct:
                LOGGER.debug(
                    "All definitions of term %s have consistent properties", term["cid"]
                )
                consistent_terms.append({
                        "package_date": package_date,
                        "term_cid": term["cid"],
                        "term_props": props,
                    })
            if not consistent:
                details = term_inconsistency_details(
                    term["raw_defs"], term["raw_cats"]
                )
                for key, val in details.items():
                    LOGGER.info(f"Inconsistency in {key}: {val}")
                    inconsistent_terms.append({
                        "package_date": package_date,
                        "term_cid": term["cid"],
                        "property": key,
                        "details": val,
                    })
            if not correct:
                details = error_details(props)
                for key, val in details.items():
                    LOGGER.info("Error in %s: %s", key, val)
                    inconsistent_terms.append({
                        "package_date": package_date,
                        "term_cid": term["cid"],
                        "property": key,
                        "details": val,
                    })
        run_single_query(
                session,
                add_props_query_multi,
                parameters={"terms": consistent_terms},
        )
        run_single_query(
            session,
            add_inconsistency_query_multi,
            parameters={"terms": inconsistent_terms},
        )
        if returned_nbr < TERM_BATCH_SIZE:
            break


def error_details(properties):
    details = {}
    # Check for unwanted quotes in any of the properties
    for prop in ["definition", "preferredTerm", "synonyms"]:
        if prop == "synonyms" and properties.get(prop) is not None:
            if properties[prop][0].startswith('"') and properties[prop][-1].endswith(
                '"'
            ):
                details[prop] = {"inconsistency": "unwanted quotes", "property": prop}
        else:
            if (
                properties.get(prop) is not None
                and properties[prop].startswith('"')
                and properties[prop].endswith('"')
            ):
                details[prop] = {"inconsistency": "unwanted quotes", "property": prop}
    return details


def term_inconsistency_details(raw_defs, cats):
    details = {}
    for prop in ["definition", "preferredTerm", "synonyms"]:
        values = set()
        for raw_def in raw_defs:
            v = raw_def.get(prop)
            if isinstance(v, list):
                v = tuple(v)
            values.add(v)
        if len(values) > 1:
            alts = {val: [] for val in values}
            for raw_def, cat in zip(raw_defs, cats):
                val = raw_def.get(prop)
                if isinstance(val, list):
                    val = tuple(val)
                cat = cat["name"]
                alts[val].append(cat)
            alternatives = {"inconsistency": "conflicting values"}
            for n, (val, cat) in enumerate(alts.items()):
                alternatives[f"value_{n+1}"] = val
                alternatives[f"catalogues_{n+1}"] = cat
            details[prop] = alternatives
    return details


def cl_inconsistency_details(raw_defs, cats):
    details = {}
    # TOD check term submission values here instead!
    for prop in ["definition", "preferredTerm", "synonyms", "submissionValue"]:
        values = set()
        for raw_def in raw_defs:
            v = raw_def.get(prop)
            if isinstance(v, list):
                v = tuple(v)
            values.add(v)
        if len(values) > 1:
            alts = {val: [] for val in values}
            for raw_def, cat in zip(raw_defs, cats):
                val = raw_def.get(prop)
                if isinstance(val, list):
                    val = tuple(val)
                cat = cat["name"]
                alts[val].append(cat)
            alternatives = {"inconsistency": "conflicting values"}
            for n, (val, cat) in enumerate(alts.items()):
                alternatives[f"value_{n+1}"] = val
                alternatives[f"catalogues_{n+1}"] = cat
            details[prop] = alternatives
    return details


def log_inconsistencies(session):
    cl_prop_count = """
        MATCH (gc:GroupedCodelist)-[hi:HAS_INCONSISTENCY]-(ip:InconsistentCodelistProperties)
        RETURN count(DISTINCT gc) as nbr_codelists, count(DISTINCT ip) as nbr_inconsistencies
    """

    cl_term_count = """
        MATCH (gc:GroupedCodelist)-[hi:HAS_INCONSISTENCY]-(it:InconsistentCodelistTerms)
        RETURN count(DISTINCT gc) as nbr_codelists, count(DISTINCT it) as nbr_inconsistencies
    """

    term_prop_count = """
        MATCH (gt:GroupedTerm)-[hi:HAS_INCONSISTENCY]-(ip:InconsistentTermProperties)
        RETURN count(DISTINCT gt) as nbr_terms, count(DISTINCT ip) as nbr_inconsistencies
    """
    codelist_props = run_single_query(session, cl_prop_count)[0]
    term_props = run_single_query(session, term_prop_count)[0]
    codelist_terms = run_single_query(session, cl_term_count)[0]
    print("Inconsistencies found:")
    print(
        f"Codelist properties: {codelist_props['nbr_inconsistencies']} inconsistencies in {codelist_props['nbr_codelists']} codelists"
    )
    print(
        f"Codelist terms: {codelist_terms['nbr_inconsistencies']} inconsistencies in {codelist_terms['nbr_codelists']} codelists"
    )
    print(
        f"Term properties: {term_props['nbr_inconsistencies']} inconsistencies in {term_props['nbr_terms']} terms"
    )


def group_data_and_identify_inconsistencies(db_driver):
    db_driver = get_neo4j_driver()
    with db_driver.session(database=NEO4J_DATABASE) as session:
        dates = get_package_dates(session)
        for package_date in dates:
            LOGGER.info(f"Processing date: {package_date}")
            merge_codelist_properties(session, package_date)
            merge_term_properties(session, package_date)
        log_inconsistencies(session)


## Step 4: Resolve term inconsistencies


def get_term_inconsistencies(session, package_date):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm)-[:HAS_INCONSISTENCY]->(ip:InconsistentTermProperties)
        MATCH (gt)-[:SOURCE_TERM_DEF]->(rt:RawTerm)-[]-(:RawCodelist)-[]-(rcat:RawCatalogue)
        RETURN gt.conceptId as term_cid, collect(ip) as inconsistencies, collect(rcat.name) as catalogues, collect(rt) as raw_terms
        """
    result = run_single_query(session, query, parameters={"package_date": package_date})
    return result


def get_cl_inconsistencies(session, package_date):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gcl:GroupedCodelist)-[:HAS_INCONSISTENCY]->(ip:InconsistentCodelistProperties)
        MATCH (gcl)-[:SOURCE_CODELIST_DEF]->(rcl:RawCodelist)-[]-(rcat:RawCatalogue)
        RETURN gcl.conceptId as codelist_cid, collect(ip) as inconsistencies, collect(rcat.name) as catalogues, collect(rcl) as raw_codelists
        """
    result = run_single_query(session, query, parameters={"package_date": package_date})
    return result


def solve_cl_term_inconsistencies(session, package_date):
    if package_date == "2018-12-21":
        # This only solves the inconsistencies caused by unwanted quotes in the 2018-12-21 package

        # Solve bad submission values where there is only one value and it has unwanted quotes
        single_vals_query = """
            MATCH (p:RawPackage {effectiveDate: "2018-12-21"})-[:HAS_GROUPED_CODELIST]-(gcl:GroupedCodelist)-[:HAS_INCONSISTENCY]->(ip:InconsistentCodelistTerms {inconsistency: "unwanted quotes"})
            WHERE (gcl)-[:SOURCE_CODELIST_DEF]->(:RawCodelist)-[]-(:RawCatalogue {name: "SEND CT 2018-12-21"})
            MATCH (gcl)-[ht:HAS_TERM]->(gt:GroupedTerm {conceptId: ip.term_cid})
            SET ht.submissionValue = replace(substring(ht.rawSubmissionValues[0], 1, size(ht.rawSubmissionValues[0]) - 2), '""', '"')
            WITH *
            MERGE (ip)-[:HAS_SOLUTION]->(sol:InconsistencySolution {desc: "Removed unwanted quotes from term submission value"}) 
            """
        run_single_query(session, single_vals_query)
        # Solve conflicting submission values where there are two value, and one has unwanted quotes
        multiple_vals_query = """
            MATCH (p:RawPackage {effectiveDate: "2018-12-21"})-[:HAS_GROUPED_CODELIST]-(gcl:GroupedCodelist)-[:HAS_INCONSISTENCY]->(ip:InconsistentCodelistTerms {inconsistency: "conflicting values"})
            WHERE (gcl)-[:SOURCE_CODELIST_DEF]->(:RawCodelist)-[]-(:RawCatalogue {name: "SEND CT 2018-12-21"})
            MATCH (gcl)-[ht:HAS_TERM]->(gt:GroupedTerm {conceptId: ip.term_cid})
            WITH ip, ht, [sv in ht.rawSubmissionValues WHERE NOT sv STARTS WITH '"' AND NOT sv ENDS WITH '"' | sv] AS clean_submvals
            SET ht.submissionValue = head(clean_submvals)
            WITH ip
            MERGE (ip)-[:HAS_SOLUTION]->(sol:InconsistencySolution {desc: "Picked a term submission value without unwanted quotes"}) 
            """
        run_single_query(session, multiple_vals_query)

    elif package_date == "2017-09-29":
        # Solve inconsistent sets of terms for the Trial Intent Type Response codelist between ProtocolCT and SDTM CT.
        # The Trial Screening term C48262 is incorrectly added in Protocol CT and should be removed.
        trial_type_terms_query = """
            MATCH (p:RawPackage {effectiveDate: "2017-09-29"})-[:HAS_GROUPED_CODELIST]-(gcl:GroupedCodelist {conceptId: "C66736"})-[:HAS_INCONSISTENCY]->(ip:InconsistentCodelistTerms {property: "terms", inconsistency: "inconsistent sets of terms"})
            MATCH (gcl)-[ht:HAS_TERM]->(gt:GroupedTerm {conceptId: "C48262"})
            DELETE ht
            WITH ip
            MERGE (ip)-[:HAS_SOLUTION]->(sol:InconsistencySolution {desc: "Removed incorrect Screening term C48262 from Trial Intent Type codelist"})
            """
        run_single_query(session, trial_type_terms_query)


def get_value_from_preferred_catalogue(values):
    for catalogue in [
        "SDTM CT",
        "ADAM CT",
        "SEND CT",
        "PROTOCOL CT",
        "DEFINE-XML CT",
        "CDASH CT",
        "COA CT",
        "QS-FT CT",
        "QRS CT",
        "DDF CT",
        "TMF CT",
        "MRCT CT",
        "GLOSSARY CT",
    ]:
        for value, cats in values.items():
            if any(cat.lower().startswith(catalogue.lower()) for cat in cats):
                return catalogue, value
    return None, None


def solve_codelist_inconsistency(cl_details):
    # Take the first definition as the base
    properties = extract_codelist_props(cl_details["raw_codelists"][0])
    solutions = {}
    for incons in cl_details["inconsistencies"]:
        property = incons["property"]
        reason = incons["inconsistency"]
        if reason != "conflicting values":
            continue
        all_values = {}
        value_nbr = 1
        while f"value_{value_nbr}" in incons:
            v = incons[f"value_{value_nbr}"]
            if isinstance(v, list):
                v = tuple(v)
            all_values[v] = incons[f"catalogues_{value_nbr}"]
            value_nbr += 1

        if property == "synonyms":
            collected = set()
            for value in all_values.keys():
                for syn in value:
                    collected.add(strip_unwanted_quotes(syn))
            properties[property] = list(collected)
            solutions[property] = {"desc": "Collected all synonyms", "reason": reason}
            continue

        # Get the value from the preferred catalogue if available
        cat, value = get_value_from_preferred_catalogue(all_values)
        if value is not None:
            properties[property] = value
            solutions[property] = {
                "desc": f"Values are different, using value from {cat}",
                "reason": reason,
            }
            continue
        LOGGER.warning(
            f"Could not resolve inconsistency for codelist {cl_details['codelist_cid']} property {property}"
        )
    return properties, solutions


def solve_term_inconsistency(term_details):
    # Take the first definition as the base
    properties = extract_term_props(term_details["raw_terms"][0])
    solutions = {}
    for incons in term_details["inconsistencies"]:
        property = incons["property"]
        reason = incons["inconsistency"]
        if reason != "conflicting values":
            continue
        all_values = {}
        value_nbr = 1
        while f"value_{value_nbr}" in incons:
            v = incons[f"value_{value_nbr}"]
            if isinstance(v, list):
                v = tuple(v)
            all_values[v] = incons[f"catalogues_{value_nbr}"]
            value_nbr += 1

        if property == "synonyms":
            collected = set()
            for value in all_values.keys():
                for syn in value:
                    collected.add(strip_unwanted_quotes(syn))
            properties[property] = list(collected)
            solutions[property] = {"desc": "Collected all synonyms", "reason": reason}
            continue

        # Get the value from the preferred catalogue if available
        cat, value = get_value_from_preferred_catalogue(all_values)
        if value is not None:
            properties[property] = value
            solutions[property] = {
                "desc": f"Values are different, using value from {cat}",
                "reason": reason,
            }
            continue
        LOGGER.warning(
            f"Could not resolve inconsistency for term {term_details['term_cid']} property {property}"
        )
    return properties, solutions


def solve_codelist_error(cl_details, properties=None):
    # Take the first definition as the base
    if properties is None:
        properties = extract_term_props(cl_details["raw_codelists"][0])
    solutions = {}
    for incons in cl_details["inconsistencies"]:
        property = incons["property"]
        reason = incons["inconsistency"]
        # Many things in SEND 2018-12-21 have unwanted extra quotes
        if (
            any(
                cat.lower().startswith("send ct 2018-12-21")
                for cat in cl_details["catalogues"]
            )
            and reason == "unwanted quotes"
        ):
            if property == "synonyms":
                if (
                    properties.get(property) is not None
                    and properties[property][0].startswith('"')
                    and properties[property][-1].endswith('"')
                ):
                    properties[property] = [
                        strip_unwanted_quotes(syn) for syn in properties[property]
                    ]
                    solutions[property] = {
                        "desc": "Ignoring data value with extra quotes from package SEND CT 2018-12-21",
                        "errortype": reason,
                    }
                else:
                    solutions[property] = {
                        "desc": "Error was already solved by a previous step",
                        "errortype": reason,
                    }
            else:
                if (
                    isinstance(properties[property], str)
                    and properties[property].startswith('"')
                    and properties[property].endswith('"')
                ):
                    properties[property] = strip_unwanted_quotes(properties[property])
                    solutions[property] = {
                        "desc": "Ignoring data value with extra quotes from package SEND CT 2018-12-21",
                        "errortype": reason,
                    }
                else:
                    solutions[property] = {
                        "desc": "Error was already solved by a previous step",
                        "errortype": reason,
                    }
    return properties, solutions


def solve_term_error(term_details, properties=None):
    # Take the first definition as the base
    if properties is None:
        properties = extract_term_props(term_details["raw_terms"][0])
    solutions = {}
    for incons in term_details["inconsistencies"]:
        property = incons["property"]
        reason = incons["inconsistency"]
        # Many things in SEND 2018-12-21 have unwanted extra quotes
        if (
            any(
                cat.lower().startswith("send ct 2018-12-21")
                for cat in term_details["catalogues"]
            )
            and reason == "unwanted quotes"
        ):
            if property == "synonyms":
                if (
                    properties.get(property) is not None
                    and properties[property][0].startswith('"')
                    and properties[property][-1].endswith('"')
                ):
                    properties[property] = [
                        strip_unwanted_quotes(syn) for syn in properties[property]
                    ]
                    solutions[property] = {
                        "desc": "Ignoring data value with extra quotes from package SEND CT 2018-12-21",
                        "errortype": reason,
                    }
                else:
                    solutions[property] = {
                        "desc": "Error was already solved by a previous step",
                        "errortype": reason,
                    }
            else:
                if properties[property].startswith('"') and properties[
                    property
                ].endswith('"'):
                    properties[property] = strip_unwanted_quotes(properties[property])
                    solutions[property] = {
                        "desc": "Ignoring data value with extra quotes from package SEND CT 2018-12-21",
                        "errortype": reason,
                    }
                else:
                    solutions[property] = {
                        "desc": "Error was already solved by a previous step",
                        "errortype": reason,
                    }
    return properties, solutions


def mark_codelist_inconsistency_solved(
    session, package_date, codelist_cid, property, solution
):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gcl:GroupedCodelist {conceptId: $codelist_cid})-[:HAS_INCONSISTENCY]->(ip:InconsistentCodelistProperties {inconsistency: "conflicting values", property: $property})
        MERGE (ip)-[:HAS_SOLUTION]->(s:InconsistencySolution {solution: $solution})
        """
    run_single_query(
        session,
        query,
        parameters={
            "package_date": package_date,
            "codelist_cid": codelist_cid,
            "property": property,
            "solution": solution,
        },
    )


def mark_codelist_error_solved(
    session, package_date, codelist_cid, property, solution, errortype
):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gt:GroupedCodelist {conceptId: $codelist_cid})-[:HAS_INCONSISTENCY]->(ip:InconsistentCodelistProperties {inconsistency: $errortype, property: $property})
        MERGE (ip)-[:HAS_SOLUTION]->(s:InconsistencySolution {solution: $solution})
        """
    run_single_query(
        session,
        query,
        parameters={
            "package_date": package_date,
            "codelist_cid": codelist_cid,
            "property": property,
            "solution": solution,
            "errortype": errortype,
        },
    )


def mark_term_inconsistency_solved(session, package_date, term_cid, property, solution):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: $term_cid})-[:HAS_INCONSISTENCY]->(ip:InconsistentTermProperties {inconsistency: "conflicting values", property: $property})
        MERGE (ip)-[:HAS_SOLUTION]->(s:InconsistencySolution {solution: $solution})
        """
    run_single_query(
        session,
        query,
        parameters={
            "package_date": package_date,
            "term_cid": term_cid,
            "property": property,
            "solution": solution,
        },
    )


def mark_term_error_solved(
    session, package_date, term_cid, property, solution, errortype
):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: $term_cid})-[:HAS_INCONSISTENCY]->(ip:InconsistentTermProperties {inconsistency: $errortype, property: $property})
        MERGE (ip)-[:HAS_SOLUTION]->(s:InconsistencySolution {solution: $solution})
        """
    run_single_query(
        session,
        query,
        parameters={
            "package_date": package_date,
            "term_cid": term_cid,
            "property": property,
            "solution": solution,
            "errortype": errortype,
        },
    )


def save_cleaned_codelist_properties(session, package_date, codelist_cid, properties):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gt:GroupedCodelist {conceptId: $codelist_cid})
        MERGE (gt)-[:HAS_GROUPED_PROPERTIES]->(props:GroupedCodelistProperties)
        SET props += $properties
        """
    run_single_query(
        session,
        query,
        parameters={
            "package_date": package_date,
            "codelist_cid": codelist_cid,
            "properties": properties,
        },
    )


def save_cleaned_term_properties(session, package_date, term_cid, properties):
    query = """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: $term_cid})
        MERGE (gt)-[:HAS_GROUPED_PROPERTIES]->(props:GroupedTermProperties)
        SET props += $properties
        """
    run_single_query(
        session,
        query,
        parameters={
            "package_date": package_date,
            "term_cid": term_cid,
            "properties": properties,
        },
    )


def resolve_codelist_inconsistencies_for_date(session, package_date):
    cls = get_cl_inconsistencies(session, package_date)
    for cl in cls:
        properties, solutions = solve_codelist_inconsistency(cl)
        for property, solution in solutions.items():
            mark_codelist_inconsistency_solved(
                session, package_date, cl["codelist_cid"], property, solution["desc"]
            )
        save_cleaned_codelist_properties(
            session, package_date, cl["codelist_cid"], properties
        )
        properties, solutions = solve_codelist_error(cl, properties=properties)
        for property, solution in solutions.items():
            mark_codelist_error_solved(
                session,
                package_date,
                cl["codelist_cid"],
                property,
                solution["desc"],
                solution["errortype"],
            )
        save_cleaned_codelist_properties(
            session, package_date, cl["codelist_cid"], properties
        )
    solve_cl_term_inconsistencies(session, package_date)


def resolve_term_inconsistencies_for_date(session, package_date):
    terms = get_term_inconsistencies(session, package_date)
    for term in terms:
        properties, solutions = solve_term_inconsistency(term)
        for property, solution in solutions.items():
            mark_term_inconsistency_solved(
                session, package_date, term["term_cid"], property, solution["desc"]
            )
        save_cleaned_term_properties(
            session, package_date, term["term_cid"], properties
        )
        properties, solutions = solve_term_error(term, properties=properties)
        for property, solution in solutions.items():
            mark_term_error_solved(
                session,
                package_date,
                term["term_cid"],
                property,
                solution["desc"],
                solution["errortype"],
            )
        save_cleaned_term_properties(
            session, package_date, term["term_cid"], properties
        )


def log_unsolved_inconsistencies(session):
    cl_prop_count = """
        MATCH (gc:GroupedCodelist)-[hi:HAS_INCONSISTENCY]-(ip:InconsistentCodelistProperties) WHERE NOT (ip)-[:HAS_SOLUTION]->()
        RETURN count(DISTINCT gc) as nbr_codelists, count(DISTINCT ip) as nbr_inconsistencies
    """

    cl_term_count = """
        MATCH (gc:GroupedCodelist)-[hi:HAS_INCONSISTENCY]-(it:InconsistentCodelistTerms) WHERE NOT (it)-[:HAS_SOLUTION]->()
        RETURN count(DISTINCT gc) as nbr_codelists, count(DISTINCT it) as nbr_inconsistencies
    """

    term_prop_count = """
        MATCH (gt:GroupedTerm)-[hi:HAS_INCONSISTENCY]-(ip:InconsistentTermProperties) WHERE NOT (ip)-[:HAS_SOLUTION]->()
        RETURN count(DISTINCT gt) as nbr_terms, count(DISTINCT ip) as nbr_inconsistencies
    """
    codelist_props = run_single_query(session, cl_prop_count)[0]
    term_props = run_single_query(session, term_prop_count)[0]
    codelist_terms = run_single_query(session, cl_term_count)[0]
    print("Unsolved inconsistencies found:")
    print(
        f"Codelist properties: {codelist_props['nbr_inconsistencies']} inconsistencies in {codelist_props['nbr_codelists']} codelists"
    )
    print(
        f"Codelist terms: {codelist_terms['nbr_inconsistencies']} inconsistencies in {codelist_terms['nbr_codelists']} codelists"
    )
    print(
        f"Term properties: {term_props['nbr_inconsistencies']} inconsistencies in {term_props['nbr_terms']} terms"
    )


def resolve_inconsistencies(db_driver):
    with db_driver.session(database=NEO4J_DATABASE) as session:
        dates = get_package_dates(session)
        for package_date in dates:
            LOGGER.info("Processing date: %s", package_date)
            resolve_codelist_inconsistencies_for_date(session, package_date)
            resolve_term_inconsistencies_for_date(session, package_date)
        log_unsolved_inconsistencies(session)


## Step 5: Build up the history for codelists


def create_codelist_nodes(session):
    query = """
        MATCH (gc:GroupedCodelist) WITH DISTINCT gc.conceptId as cid, collect(gc) as gcs
        MERGE (vc:VersionedCodelist {conceptId: cid})
        FOREACH (n IN gcs | MERGE (vc)-[:HAS_SOURCE_VERSION]->(n))
        """
    run_single_query(session, query)


def get_versioned_codelist_cids(session, start, nbr):
    query = "MATCH (vc:VersionedCodelist) RETURN vc.conceptId as cid ORDER BY cid SKIP $start LIMIT $nbr"
    result = run_single_query(session, query, parameters={"start": start, "nbr": nbr})
    return [record["cid"] for record in result]


def get_codelist_props_hash(props):
    hashable_props = deepcopy(props)
    if "synonyms" in hashable_props:
        hashable_props["synonyms"] = frozenset(sorted(hashable_props["synonyms"]))
    h = hash(frozenset(hashable_props.items()))
    return h


def get_codelist_definitions(session, codelist_cid):
    query = """
        MATCH (vc:VersionedCodelist {conceptId: $codelist_cid})-[:HAS_SOURCE_VERSION]->(gc:GroupedCodelist)-[:HAS_GROUPED_PROPERTIES]->(gp)
        MATCH (gc)-[:HAS_GROUPED_CODELIST]-(rp:RawPackage)
        RETURN rp.effectiveDate as package_date, properties(gp) as props 
    """
    result = run_single_query(session, query, parameters={"codelist_cid": codelist_cid})
    return result


def process_single_codelist(session, term_cid, all_package_dates):
    definitions = get_codelist_definitions(session, term_cid)
    distinct_defs = {}
    for definition in definitions:
        h = get_codelist_props_hash(definition["props"])
        if h not in distinct_defs:
            distinct_defs[h] = {
                "dates": [definition["package_date"]],
                "props": definition["props"],
            }
        else:
            distinct_defs[h]["dates"].append(definition["package_date"])
    versioned = []
    prev_hash = None
    next_version = 1
    for p_date in all_package_dates:
        for h, def_data in distinct_defs.items():
            if p_date in def_data["dates"]:
                if prev_hash is None:
                    # First version
                    versioned.append(
                        {
                            "version": {"start_date": p_date, "version": next_version},
                            "props": def_data["props"],
                            "dates": [p_date],
                        }
                    )
                    prev_hash = h
                    next_version += 1
                    break
                elif prev_hash != h:
                    # Something changed from the previous version
                    # Retire the previous version if needed
                    LOGGER.debug("New version needed: %s", def_data["props"])
                    if "end_date" not in versioned[-1]["version"]:
                        LOGGER.debug("Retiring previous version: %s", versioned[-1])
                        versioned[-1]["version"]["end_date"] = p_date
                    versioned.append(
                        {
                            "version": {"start_date": p_date, "version": next_version},
                            "props": def_data["props"],
                            "dates": [p_date],
                        }
                    )
                    prev_hash = h
                    next_version += 1
                    break
                elif "end_date" in versioned[-1]["version"]:
                    LOGGER.debug(
                        "Resurrect previous retired version: %s", def_data["props"]
                    )
                    # The previous version was retired, create a new one to bring the term back to active
                    versioned.append(
                        {
                            "version": {"start_date": p_date, "version": next_version},
                            "props": def_data["props"],
                            "dates": [p_date],
                        }
                    )
                    prev_hash = h
                    next_version += 1
                    break
                else:
                    # No change from the previous version
                    versioned[-1]["dates"].append(p_date)
                    break
            elif len(versioned) == 0:
                # This codelist hasn't been created yet in the current package.
                # This will happen frequently if the script is run more than once.
                pass
            else:
                # The codelist has been retired
                # if "end_date" not in versioned[-1]["version"]:
                #    versioned[-1]["version"]["end_date"] = p_date
                LOGGER.debug(
                    "Codelist is not in the current package, safe to retire? %s",
                    def_data["props"],
                )
    return versioned


def build_codelist_history(session):
    all_package_dates = sorted(
        get_package_dates(session),
        key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"),
    )
    start = 0
    total_nbr_codelists = 0
    total_nbr_versions = 0
    while True:
        codelist_cids = get_versioned_codelist_cids(session, start, CODELIST_BATCH_SIZE)
        returned_nbr = len(codelist_cids)
        LOGGER.info("Process codelists: start: %s, nbr: %s", start, returned_nbr)
        if returned_nbr == 0:
            break
        start += returned_nbr
        total_nbr_codelists += returned_nbr


        for codelist_cid in codelist_cids:
            versions = process_single_codelist(session, codelist_cid, all_package_dates)
            store_codelist_versions(session, codelist_cid, versions)
            total_nbr_versions += len(versions)
    LOGGER.info(
        "Total codelists processed: %s, total versions created: %s",
        total_nbr_codelists,
        total_nbr_versions,
    )


def store_codelist_versions(session, codelist_cid, versions):
    query = """
        MATCH (vc:VersionedCodelist {conceptId: $codelist_cid})-[:HAS_SOURCE_VERSION]->(gc:GroupedCodelist)
        UNWIND $versions as codelist_ver
            MERGE (vc)-[hv:HAS_VERSION {version: codelist_ver.version.version}]->(v:CodelistVersion)
            SET v = codelist_ver.props
            SET hv = codelist_ver.version
            WITH v, codelist_ver, gc
            UNWIND codelist_ver.dates as date
                MATCH (gcp:GroupedCodelistProperties)<-[:HAS_GROUPED_PROPERTIES]-(gc)-[:HAS_GROUPED_CODELIST]-(rp:RawPackage {effectiveDate: date})
                MERGE (v)-[:FROM_PACKAGE]->(gcp)
        """
    run_single_query(
        session, query, parameters={"codelist_cid": codelist_cid, "versions": versions}
    )


def handle_codelist_history(db_driver):
    with db_driver.session(database=NEO4J_DATABASE) as session:
        create_codelist_nodes(session)
        build_codelist_history(session)


## Step 6: Build history for terms


def create_term_nodes(session):
    query = """
        MATCH (gt:GroupedTerm) WITH DISTINCT gt.conceptId as cid, collect(gt) as gts
        MERGE (vt:VersionedTerm {conceptId: cid})
        FOREACH (n IN gts | MERGE (vt)-[:HAS_SOURCE_VERSION]->(n))
        """
    run_single_query(session, query)

def get_versioned_terms_with_definitions(session, start, nbr):
    query = """
        MATCH (vc:VersionedTerm) WITH vc ORDER BY vc.conceptId SKIP $start LIMIT $nbr
        CALL (vc) {
            MATCH (vc)-[:HAS_SOURCE_VERSION]->(gt:GroupedTerm)-[:HAS_GROUPED_PROPERTIES]->(gp)
            MATCH (gt)-[:HAS_GROUPED_TERM]-(rp:RawPackage)
            RETURN rp.effectiveDate as package_date, properties(gp) as props
        }
        RETURN vc.conceptId AS cid, collect({package_date: package_date, props: props}) as definitions
    """
    result = run_single_query(session, query, parameters={"start": start, "nbr": nbr})
    return result


def get_term_props_hash(props):
    hashable_props = deepcopy(props)
    if "synonyms" in hashable_props:
        hashable_props["synonyms"] = frozenset(sorted(hashable_props["synonyms"]))
    h = hash(frozenset(hashable_props.items()))
    return h


def process_single_term(session, term, all_package_dates):
    definitions = term["definitions"]

    distinct_defs = {}
    for definition in definitions:
        h = get_term_props_hash(definition["props"])
        if h not in distinct_defs:
            distinct_defs[h] = {
                "dates": [definition["package_date"]],
                "props": definition["props"],
            }
        else:
            distinct_defs[h]["dates"].append(definition["package_date"])
    versioned = []
    prev_hash = None
    next_version = 1
    for p_date in all_package_dates:
        for h, def_data in distinct_defs.items():
            if p_date in def_data["dates"]:
                if prev_hash is None:
                    # First version
                    versioned.append(
                        {
                            "version": {"start_date": p_date, "version": next_version},
                            "props": def_data["props"],
                            "dates": [p_date],
                        }
                    )
                    prev_hash = h
                    next_version += 1
                    break
                elif prev_hash != h:
                    # Something changed from the previous version
                    # Retire the previous version if needed
                    LOGGER.debug("New version needed: %s", def_data["props"])
                    if "end_date" not in versioned[-1]["version"]:
                        LOGGER.debug("Retiring previous version: %s", versioned[-1])
                        versioned[-1]["version"]["end_date"] = p_date
                    versioned.append(
                        {
                            "version": {"start_date": p_date, "version": next_version},
                            "props": def_data["props"],
                            "dates": [p_date],
                        }
                    )
                    prev_hash = h
                    next_version += 1
                    break
                elif "end_date" in versioned[-1]["version"]:
                    LOGGER.debug(
                        "Resurrect previous retired version", def_data["props"]
                    )
                    # The previous version was retired, create a new one to bring the term back to active
                    versioned.append(
                        {
                            "version": {"start_date": p_date, "version": next_version},
                            "props": def_data["props"],
                            "dates": [p_date],
                        }
                    )
                    prev_hash = h
                    next_version += 1
                    break
                else:
                    # No change from the previous version
                    versioned[-1]["dates"].append(p_date)
                    break
            elif len(versioned) == 0:
                # This term hasn't been created yet in the current package
                pass
            else:
                # The term has been retired
                # if "end_date" not in versioned[-1]["version"]:
                #    versioned[-1]["version"]["end_date"] = p_date
                LOGGER.debug(
                    "Term is not in the current package, safe to retire? %s",
                    def_data["props"],
                )
    return versioned


def store_term_versions_multi(session, term_versions):
    query = """
        UNWIND $term_versions as term
        MATCH (vt:VersionedTerm {conceptId: term.cid})-[:HAS_SOURCE_VERSION]->(gt:GroupedTerm)
        UNWIND term.versions as term_ver
            MERGE (vt)-[hv:HAS_VERSION {version: term_ver.version.version}]->(v:TermVersion)
            SET v = term_ver.props
            SET hv = term_ver.version
            WITH v, term_ver, gt
            UNWIND term_ver.dates as date
                MATCH (gtp:GroupedTermProperties)<-[:HAS_GROUPED_PROPERTIES]-(gt)-[:HAS_GROUPED_TERM]-(rp:RawPackage {effectiveDate: date})
                MERGE (v)-[:FROM_PACKAGE]->(gtp)
        """
    run_single_query(
        session, query, parameters={"term_versions": term_versions}
    )


def build_term_history(session):
    all_package_dates = sorted(
        get_package_dates(session),
        key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"),
    )
    start = 0
    total_nbr_terms = 0
    total_nbr_versions = 0
    while True:
        terms = get_versioned_terms_with_definitions(session, start, TERM_BATCH_SIZE)
        returned_nbr = len(terms)
        LOGGER.info("Process terms: start: %s, nbr: %s", start, returned_nbr)
        if returned_nbr == 0:
            break
        start += returned_nbr

        term_versions = []
        for term in terms:
            versions = process_single_term(session, term, all_package_dates)
            term_versions.append({"cid": term["cid"], "versions": versions})
            total_nbr_terms += 1
            total_nbr_versions += len(versions)
        store_term_versions_multi(session, term_versions)
    LOGGER.info("Created %s versions for %s terms", total_nbr_versions, total_nbr_terms)


def handle_term_history(db_driver):
    with db_driver.session(database=NEO4J_DATABASE) as session:
        create_term_nodes(session)
        build_term_history(session)


## Step 7: Add terms to versioned codelists


def get_terms_for_codelist_cid(session, codelist_cid):
    query = """
        MATCH (vcl:VersionedCodelist {conceptId: $codelist_cid})
        MATCH (vcl)--(gcl:GroupedCodelist)--(rp:RawPackage)
        OPTIONAL MATCH (gcl)-[ht:HAS_TERM]-(gt:GroupedTerm)--(vt:VersionedTerm)
        WITH vcl, gcl, rp, ht.submissionValue as submval, gt, vt
        RETURN * ORDER BY date(rp.effectiveDate)
        """
    result = run_single_query(session, query, parameters={"codelist_cid": codelist_cid})
    return result


def add_terms_to_single_codelist(session, codelist_cid):
    cl_terms = get_terms_for_codelist_cid(session, codelist_cid)
    termdata = {}
    all_dates = set(term["rp"]["effectiveDate"] for term in cl_terms)
    # Get term submission value for each package date
    for term in cl_terms:
        date = term["rp"]["effectiveDate"]
        if term["gt"] is not None:
            cid = term["vt"]["conceptId"]
            if cid not in termdata:
                termdata[cid] = {}
            termdata[cid][date] = term["submval"]
    # Fill in None for the missing package dates
    for date in all_dates:
        for cid, term in termdata.items():
            if date not in term:
                term[date] = None
    sorted_terms = {}
    for cid, term in termdata.items():
        submvals = sorted(term.items(), key=lambda x: x[0])
        for date, submval in submvals:
            if submval is not None and cid not in sorted_terms:
                # First version
                sorted_terms[cid] = [{"submval": submval, "start_date": date}]
            elif submval is not None:
                # New version?
                existing = sorted_terms[cid][-1]
                if existing["submval"] != submval:
                    # Different value, new version
                    if "end_date" not in existing:
                        existing["end_date"] = date
                    sorted_terms[cid].append({"submval": submval, "start_date": date})
            elif submval is None and cid in sorted_terms:
                # This term was removed, retire the previous version
                if "end_date" not in sorted_terms[cid][-1]:
                    sorted_terms[cid][-1]["end_date"] = date

    terms_to_add = []
    for term_cid, submvals in sorted_terms.items():
        for submval in submvals:
            terms_to_add.append({
                "term_cid": term_cid,
                "submval": submval.get("submval"),
                "start_date": submval["start_date"],
                "end_date": submval.get("end_date"),
            })
            # Add the term to the codelist
            #link_term_to_codelist(session, codelist_cid, term_cid, submval)
    link_terms_to_codelist(session, codelist_cid, terms_to_add)

def link_term_to_codelist(session, codelist_cid, term_cid, submval):
    query = """
        MATCH (vcl:VersionedCodelist {conceptId: $codelist_cid})
        MATCH (vt:VersionedTerm {conceptId: $term_cid})
        MERGE (vcl)-[ht:HAS_TERM {submissionValue: $submval}]->(vt)
        ON CREATE SET ht.start_date = $start_date
        SET ht.end_date = $end_date
        """
    run_single_query(
        session,
        query,
        parameters={
            "codelist_cid": codelist_cid,
            "term_cid": term_cid,
            "submval": submval.get("submval"),
            "start_date": submval["start_date"],
            "end_date": submval.get("end_date"),
        },
    )

def link_terms_to_codelist(session, codelist_cid, terms_data):
    query = """
        MATCH (vcl:VersionedCodelist {conceptId: $codelist_cid})
        UNWIND $terms_data as term_entry
        MATCH (vt:VersionedTerm {conceptId: term_entry.term_cid})
        MERGE (vcl)-[ht:HAS_TERM {submissionValue: term_entry.submval}]->(vt)
        ON CREATE SET ht.start_date = term_entry.start_date
        SET ht.end_date = term_entry.end_date
        """
    run_single_query(
        session,
        query,
        parameters={
            "codelist_cid": codelist_cid,
            "terms_data": terms_data
        },
    )


# Add the terms fo the versioned codelists
def add_terms_to_versioned_codelists(session):
    start = 0
    while True:
        codelist_cids = get_versioned_codelist_cids(session, start, CODELIST_BATCH_SIZE)
        returned_nbr = len(codelist_cids)
        LOGGER.info("Process codelists: start: %s, nbr: %s", start, returned_nbr)
        start += returned_nbr

        for codelist_cid in codelist_cids:
            add_terms_to_single_codelist(session, codelist_cid)
        if returned_nbr < CODELIST_BATCH_SIZE:
            break


def add_versioned_codelist_terms(db_driver):
    with db_driver.session(database=NEO4J_DATABASE) as session:
        add_terms_to_versioned_codelists(session)


# Step 8: Connect name and code codelists based on SDTM Paired Codelist Excel file from CDISC


def extract_columns_from_excel(file_path, sheet_name):
    try:
        LOGGER.info("Extracting codelist pairs from Excel file: %s", file_path)
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook[sheet_name]
        data = []
        # Get the headers from the first row
        headers = [cell.value for cell in sheet[1]]
        cid_index = headers.index("Code")
        submval_index = headers.index("CDISC Submission Value")
        it = enumerate(sheet.iter_rows(values_only=True, min_row=2))
        all_cids = set()
        for r1, row in it:
            cid1 = row[cid_index]
            submval1 = row[submval_index]
            # get also the next row from the iterator
            r2, row = next(it)
            cid2 = row[cid_index]
            submval2 = row[submval_index]

            # Some entries are dupliated, handle that
            if cid1 == cid2:
                r3, row = next(it)
                cid3 = row[cid_index]
                submval3 = row[submval_index]

                r4, row = next(it)
                cid2 = row[cid_index]
                submval2 = row[submval_index]
                if cid2 != cid3:
                    raise RuntimeError(
                        f"Error in Excel file at row {r1+2} - {r4+2}: {cid2} != {cid3}"
                    )
                LOGGER.warning(
                    "Duplicated entries on lines %s - %s removed for codelists %s: %s and %s: %s",
                    r1 + 2,
                    r4 + 2,
                    cid1,
                    submval1,
                    cid2,
                    submval2,
                )
                r2 = r4

            # Submission value pairs follow either the pattern nnnn + nnnnCD or nnnnTN + nnnnTC
            # Figure out which is the name and which is the code and check that they match
            # the two rows we have are name and code, but we don't trust that the order is always the same
            if len(submval1) == len(submval2) + 2:
                name = submval2
                code = submval1
                name_cid = cid2
                code_cid = cid1
                name_base = name
                code_base = code[:-2]
            elif len(submval2) == len(submval1) + 2:
                name = submval1
                code = submval2
                name_cid = cid1
                code_cid = cid2
                name_base = name
                code_base = code[:-2]
            elif submval1.endswith("TN") and submval2.endswith("TC"):
                name = submval1
                code = submval2
                name_cid = cid1
                code_cid = cid2
                code_base = code[:-2]
                name_base = name[:-2]
            elif submval2.endswith("TN") and submval1.endswith("TC"):
                name = submval2
                code = submval1
                name_cid = cid2
                code_cid = cid1
                code_base = code[:-2]
                name_base = name[:-2]
            elif submval1.endswith("PN") and submval2.endswith("PC"):
                name = submval1
                code = submval2
                name_cid = cid1
                code_cid = cid2
                code_base = code[:-2]
                name_base = name[:-2]
            elif submval2.endswith("PN") and submval1.endswith("PC"):
                name = submval2
                code = submval1
                name_cid = cid2
                code_cid = cid1
                code_base = code[:-2]
                name_base = name[:-2]
            else:
                LOGGER.warning(
                    "Skipping unknown pattern: %s and %s on rows %s - %s",
                    submval1,
                    submval2,
                    r1 + 2,
                    r2 + 2,
                )
                continue
            if name_base != code_base:
                LOGGER.warning(
                    "Skipping non-matching submission values on rows %s - %s: %s != %s",
                    r1 + 2,
                    r2 + 2,
                    name_base,
                    code_base,
                )
                continue

            # Check that no codelist is paired more than once
            if name_cid in all_cids:
                LOGGER.warning("Skipping already paired name codelist: %s", name_cid)
                continue
            if code_cid in all_cids:
                LOGGER.warning("Skipping already paired code codelist: %s", code_cid)
                continue
            all_cids.add(name_cid)
            all_cids.add(code_cid)

            # Ok, add the pair
            data.append(
                {
                    "name_cid": name_cid,
                    "name": name,
                    "code_cid": code_cid,
                    "code:": code,
                }
            )
        LOGGER.debug("Extracted %s codelist pairs from Excel", len(data))
        return data
    except Exception as e:
        LOGGER.warning("Error occurred while extracting columns from Excel: %s", e)
        return None


def get_last_file_with_prefix(directory, prefix):
    files = [file for file in os.listdir(directory) if file.startswith(prefix)]
    files.sort()
    if files:
        return files[-1]
    else:
        return None


def connect_codelists(session, pair):
    query = """
        MATCH (nc:VersionedCodelist {conceptId: $pair.name_cid})
        MATCH (cc:VersionedCodelist {conceptId: $pair.code_cid})
        MERGE (nc)-[:PAIRED_WITH_CODES]->(cc)
        """
    run_single_query(session, query, parameters={"pair": pair})


def connect_name_and_code_codelists(db_driver):
    directory = "CDISC_xls"
    all_pairs = []

    # Extract the pairs from the three relevant Excel files
    for prefix, sheet_name in [
        ("SDTM_paired_view", "SDTM Paired Codelist Metadata"),
        ("ADaM_paired_view", "ADaM Paired Codelist Metadata"),
        ("SEND_paired_view", "SEND Paired Codelist Metadata"),
    ]:
        filename = get_last_file_with_prefix(directory, prefix)
        if filename is None:
            LOGGER.warning("No file found with prefix: %s", prefix)
            continue
        filepath = os.path.join(directory, filename)
        pairs = extract_columns_from_excel(filepath, sheet_name)
        if pairs is not None:
            all_pairs.extend(pairs)

    # drop any duplicated pairs
    seen = set()
    pairs = []
    for pair in all_pairs:
        t = (pair["name_cid"], pair["code_cid"])
        if t not in seen:
            seen.add(t)
            pairs.append(pair)

    # Connect the codelists in the database
    with db_driver.session(database=NEO4J_DATABASE) as session:
        for pair in pairs:
            connect_codelists(session, pair)


def make_sponsor_term_names(terms_data):
    for term_data in terms_data:
        make_sponsor_term_name(term_data)


def _get_first_submission_value_for_codelist_cids(term_data, codelist_cids):
    """
    Get the submission values for the given codelist CIDs from the term data.
    Returns a dictionary with codelist CID as key and a list of submission values as value.
    """
    for cid in codelist_cids:
        try:
            idx = term_data["cl_cid"].index(cid)
            # Get the submission values for this codelist CID
            return term_data["submvals"][idx]
        except ValueError:
            pass
    return None

def make_sponsor_term_name(term_data):
    """
    Add a sponsor name for a term based on its preferred term or submission value.
    """
    # start with the CDISC preferred term
    newname = term_data["term_name"]
    # Clean by removing any trailing space or newline
    newname = newname.strip(" \n")
    method = "Use preferred term"

    if term_data["term_cid"] == "C48262":
        # Rename Trial Screening to just Screening
        newname = "Screening"
        method = "Special case for 'Trial Screening'"

    elif term_data["term_cid"] == "C99158":
        # Rename Clinical Study Follow-up to just Follow-up
        newname = "Follow-up"
        method = "Special case for 'Clinical Study Follow-up'"

    # Updates related to codelist C66737 - Trial Phase Response. ICH M11 preferred term do not match NCI/CDISC preferred term
    elif term_data["term_cid"] == "C54721":
        # Rename Early Phase I -> Early Phase 1
         newname = "Early Phase 1"
         method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C15600":
        # Rename Phase I Trial -> Phase 1
         newname = "Phase 1"
         method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C15693":
        # Rename Phase I/II Trial ->  Phase 1/Phase 2
        newname = "Phase 1/Phase 2"
        method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C198366":
        # Rename Phase I/II/III Trial ->  Phase 1/Phase 2/Phase 3
        newname = "Phase 1/Phase 2/Phase 3"
        method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C198367":
        # Rename Phase I/III Trial -> Phase 1/Phase 3
        newname = "Phase 1/Phase 3"
        method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C15601":
        # Rename Phase II Trial -> Phase 2
        newname = "Phase 2"
        method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C15694":
        # Rename Phase II/III Trial -> Phase 2/Phase 3
        newname = "Phase 2/Phase 3"
        method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C15602":
        # Rename Phase III Trial -> Phase 3
        newname = "Phase 3"
        method = "Special case for 'Trial Phase Response'"
    elif term_data["term_cid"] == "C15603":
        # Rename Phase IV Trial -> Phase 4
        newname = "Phase 4"
        method = "Special case for 'Trial Phase Response'"

    elif "C99077" in term_data["cl_cid"]:
        # Study type codelist

        # Remove "Study" from end
        newname = re.sub(r" Study$", "", newname)
        method = "Use preferred term without 'Study' ending"

    elif "C99079" in term_data["cl_cid"]:
        # Epoch codelist
        # Remove "Epoch", "Period" or "Study Epoch" from end
        # or "Investigational" from start
        newname = re.sub(r"^(Investigational )", "", newname)
        newname = re.sub(r" (Epoch|Period|Study Epoch)$", "", newname)
        method = "Use preferred term without 'Epoch', 'Period' or 'Study Epoch' ending or leading 'Investigational'"

    elif "C66736" in term_data["cl_cid"]:
        # Trial type codelist

        # Remove "Study" or "Trial" from end
        newname = re.sub(r" (Study|Trial)$", "", newname)
        method = "Use preferred term without 'Study' or 'Trial' ending"

    elif "C66785" in term_data["cl_cid"]:
        # Control type codelist

        # Remove "Control" from end
        newname = re.sub(r" Control$", "", newname)
        method = "Use preferred term without 'Control' ending"

    elif "C66735" in term_data["cl_cid"]:
        # Trial Blinding Schema codelist

        # Remove "Study" from end
        newname = re.sub(r" Study$", "", newname)
        method = "Use preferred term without 'Study' ending"

    elif "C99076" in term_data["cl_cid"]:
        # Intervention Model Response codelist

        # Remove "Study" from end
        newname = re.sub(r" Study$", "", newname)
        method = "Use preferred term without 'Study' ending"

    elif "C188725" in term_data["cl_cid"]:
        # Objective level codelist

        # Remove the leading "Trial " if present
        newname = re.sub(r"^Trial ", "", newname)
        method = "Use preferred term without leading 'Trial'"

    elif submval := _get_first_submission_value_for_codelist_cids(term_data, ("C66729", "C78420", "C78425")):
        # Main codelist:
        # - Route of Administration, C66729
        # Subsets:
        # - Concomitant Medication Route of Administration, C78420
        # - Exposure Route of Administration, C78425

        if newname.startswith("Administration via"):
            # If starting with "Administration via" then we use the submission value
            newname = submval.title()
            method = "Use submission value for names starting with 'Administration via'"
        else:
            # Remove "Route of Administration" at start or end.
            # When at the end, allow both a space and a dash in front.
            newname = re.sub(
                r"((\s|-)Route of Administration$|^Route of Administration )", "", newname
            )
            method = "Use preferred term without 'Route of Administration'"

    elif _get_first_submission_value_for_codelist_cids(term_data, ("C66726", "C78418", "C78426")):
        # Main codelist:
        # - Pharmaceutical Dosage Form, C66726
        # Subsets
        # - Concomitant Medication Dose Form, C78418
        # - Exposure Dose Form, C78426

        # Remove "Dosage Form" at start or end or middle
        newname = re.sub(r"^Dosage Form for", "For", newname)
        newname = re.sub(r"(\sDosage Form($|(?=\s))|^Dosage Form\s)", "", newname)
        method = "Use preferred term without 'Dosage Form'"

    elif _get_first_submission_value_for_codelist_cids(term_data, ("C71113", "C78419", "C78745")):
        # Main codelist:
        # - Frequency, C71113
        # Subsets:
        # - Concomitant Medication Dosing Frequency per Interval, C78419
        # - Exposure Dosing Frequency per Interval, C78745

        # Clean by removing any trailing period
        # Seen (so far) only for C139178: "Every Night." in sdtmct json-files from before 2019-09-27.
        newname = newname.strip(".")

        # Special cases
        if newname == "Infrequent":
            # Use the synonym "Occasional" instead
            newname = "Occasional"
            method = "Use synonym for 'Infrequent'"
        elif term_data["term_cid"] == "C64596":
            # C64596 was named "Every Evening" before 2019-06-28,
            # and after that it was changed to "QPM" (which is really the submission value).
            # We use "Every Day" as the sponsor name.
            newname = "Every Day"
            method = "Use 'Every Day' for C64596"
        else:
            # Replace "Per Day/Month" with "Daily/Monthly"
            newname = re.sub(r" Per Day$", " Daily", newname)
            newname = re.sub(r" Per Month$", " Monthly", newname)
            method = "Use preferred term with 'Per Day'/'Per Month' replaced by 'Daily'/'Monthly'"

    elif submval := _get_first_submission_value_for_codelist_cids(term_data, (
        "C71620",
        "C78417",
        "C78422",
        "C78428",
        "C78427",
        "C78429",
        "C78421",
        "C78423",
        "C78430",
        "C66770",
        "C66781",
        "C85494",
        "C128685",
        "C128686",
        "C128684",
        "C128683",
    )):
        # Main codelist:
        # - Unit, C71620
        # Subsets:
        # - Concomitant Medication Dose Units, C78417
        # - ECG Original Units, C78422
        # - Total Volume Administration Unit, C78428
        # - Unit for the Duration of Treatment Interruption, C78427
        # - Unit of Measure for Flow Rate, C78429
        # - Unit of Drug Dispensed or Returned, C78421
        # - Units for Exposure, C78423
        # - Units for Planned Exposure, C78430
        # - Units for Vital Signs Results, C66770
        # - Age Unit, C66781
        # - PK Units of Measure, C85494
        # - PK Units of Measure - Dose mg, C128685
        # - PK Units of Measure - Dose ug, C128686
        # - PK Units of Measure - Weight g, C128684
        # - PK Units of Measure - Weight kg, C128683

        # Use code submission value as name
        newname = submval
        method = "Use submission value for Unit codelists"

    term_data["sponsor_name"] = newname
    term_data["method"] = method

def list_versioned_terms(db_driver, page_size=100, page_number=1):
    query = """
        MATCH (tv:TermVersion)<-[hv:HAS_VERSION]-(vt:VersionedTerm)-[ht:HAS_TERM]-(vcl:VersionedCodelist)
        WITH 
            tv.preferredTerm as term_name,
            vt.conceptId as term_cid,
            hv.version AS term_version,
            collect(ht.submissionValue) as submvals,
            collect(vcl.conceptId) AS cl_cid
        ORDER BY term_cid, term_version
        RETURN * SKIP $skip LIMIT $limit
    """
    skip = (page_number - 1) * page_size
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(
            session, query, parameters={"skip": skip, "limit": page_size}
        )
    return result


def create_sponsor_name_nodes(db_driver, terms_data):
    query = """
        UNWIND $terms_data AS term
        MATCH (tv:TermVersion)<-[:HAS_VERSION {version: term.term_version}]->(:VersionedTerm {conceptId: term.term_cid})
        MERGE (sn:SponsorName)-[:SPONSOR_NAME_FOR]->(tv)
        SET sn.name = term.sponsor_name, sn.method = term.method
    """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        run_single_query(session, query, parameters={"terms_data": terms_data})


def add_sponsor_names_to_terms(db_driver):
    page_number = 1
    while True:
        terms_data = list_versioned_terms(db_driver, page_number=page_number, page_size=TERM_BATCH_SIZE)
        LOGGER.info("Processing page %s of %s terms for sponsor names", page_number, len(terms_data))
        if not terms_data:
            break
        make_sponsor_term_names(terms_data)
        create_sponsor_name_nodes(db_driver, terms_data)
        page_number += 1

def log_summary(db_driver):
    # Raw packages
    query = """
        MATCH (rp:RawPackage)
        WITH DISTINCT rp.effectiveDate AS effective_date
        RETURN count(effective_date) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_packages = result[0]["nbr"]
    LOGGER.info("Number of packages loaded: %s", nbr_packages)

    query = """
        MATCH (vt:VersionedTerm) RETURN count(vt) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_terms = result[0]["nbr"]
    LOGGER.info("Total number of versioned terms: %s", nbr_terms)

    query = """
        MATCH (vcl:VersionedCodelist) RETURN count(vcl) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_codelists = result[0]["nbr"]
    LOGGER.info("Total number of versioned codelists: %s", nbr_codelists)

    # Codelist property inconsistencies
    query = """
        MATCH (icp:InconsistentCodelistProperties)
        RETURN count(icp) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_inconsistencies = result[0]["nbr"]
    LOGGER.info("Number of codelist property inconsistencies found: %s", nbr_inconsistencies)

    query = """
        MATCH (icp:InconsistentCodelistProperties) WHERE NOT (icp)-[:HAS_SOLUTION]-()
        RETURN count(icp) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_inconsistencies = result[0]["nbr"]
    if nbr_inconsistencies == 0:
        LOGGER.info("All codelist property inconsistencies have been resolved.")
    else:
        LOGGER.warning("Number of unresolved codelist property inconsistencies: %s", nbr_inconsistencies)

    # Codelist term inconsistencies
    query = """
        MATCH (ict:InconsistentCodelistTerms)
        RETURN count(ict) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_inconsistencies = result[0]["nbr"]
    LOGGER.info("Number of codelist term inconsistencies found: %s", nbr_inconsistencies)

    query = """
        MATCH (ict:InconsistentCodelistTerms) WHERE NOT (ict)-[:HAS_SOLUTION]-()
        RETURN count(ict) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_inconsistencies = result[0]["nbr"]
    if nbr_inconsistencies == 0:
        LOGGER.info("All codelist term inconsistencies have been resolved.")
    else:
        LOGGER.warning("Number of unresolved codelist term inconsistencies: %s", nbr_inconsistencies)

    # Term inconsistencies
    query = """
        MATCH (itp:InconsistentTermProperties)
        RETURN count(itp) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_inconsistencies = result[0]["nbr"]
    LOGGER.info("Number of term inconsistencies found: %s", nbr_inconsistencies)

    query = """
        MATCH (itp:InconsistentTermProperties) WHERE NOT (itp)-[:HAS_SOLUTION]-()
        RETURN count(itp) as nbr
        """
    with db_driver.session(database=NEO4J_DATABASE) as session:
        result = run_single_query(session, query)
        nbr_inconsistencies = result[0]["nbr"]
    if nbr_inconsistencies == 0:
        LOGGER.info("All term inconsistencies have been resolved.")
    else:
        LOGGER.warning("Number of unresolved term inconsistencies: %s", nbr_inconsistencies)



def main():
    # Get db clear boolean argument
    parser = argparse.ArgumentParser(description="Clear CDISC staging database.")
    parser.add_argument(
        "--clear-staging-db",
        action="store_true",
        help="Clear the CDISC staging database before loading new data.",
    )
    args = parser.parse_args()
    clear_staging_db = args.clear_staging_db

    LOGGER.info(f"Creating database '{NEO4J_DATABASE}' if it does not exist")
    db_driver = get_neo4j_driver(database=None)
    create_database(db_driver, NEO4J_DATABASE, clear_db=clear_staging_db)

    db_driver = get_neo4j_driver(database=NEO4J_DATABASE)

    LOGGER.info("Step 1: create indexes")
    with db_driver.session(database=NEO4J_DATABASE) as session:
        create_indexes(session)

    LOGGER.info("Step 2: Load the raw JSON data into the database")
    process_all_packages(db_driver)

    LOGGER.info("Step 3: Group terms and codelists based on concept id")
    group_data(db_driver)

    LOGGER.info(
        "Step 4: Group term and codelist definitions and identify inconsistencies"
    )
    group_data_and_identify_inconsistencies(db_driver)

    LOGGER.info("Step 5: Resolve term inconsistencies")
    resolve_inconsistencies(db_driver)

    LOGGER.info("Step 6: Build up the history for codelists")
    handle_codelist_history(db_driver)

    LOGGER.info("Step 7: Build history for terms")
    handle_term_history(db_driver)

    LOGGER.info("Step 8: Add terms to versioned codelists")
    add_versioned_codelist_terms(db_driver)

    LOGGER.info(
        "Step 9: Connect name and code codelists based on Paired Codelist Excel files from CDISC"
    )
    connect_name_and_code_codelists(db_driver)

    LOGGER.info("Step 10: Create sponsor names for terms")
    add_sponsor_names_to_terms(db_driver)

    LOGGER.info("All steps completed successfully.")

    log_summary(db_driver)


if __name__ == "__main__":
    main()
