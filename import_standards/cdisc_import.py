import logging
import argparse
from datetime import datetime, timezone
from os import environ

from src.scripts.utils import get_sentence_case_string, create_user

from neo4j import GraphDatabase

# StudyBuilder database connection parameters
NEO4J_SB_HOST = environ.get("NEO4J_MDR_HOST")
NEO4J_SB_BOLT_PORT = environ.get("NEO4J_MDR_BOLT_PORT")
NEO4J_SB_AUTH_USER = environ.get("NEO4J_MDR_AUTH_USER")
NEO4J_SB_AUTH_PASSWORD = environ.get("NEO4J_MDR_AUTH_PASSWORD")
NEO4J_SB_DATABASE = environ.get("NEO4J_MDR_DATABASE")
NEO4J_PROTOCOL = environ.get("NEO4J_PROTOCOL", "neo4j")

# CDISC staging database connection parameters
NEO4J_STAGING_HOST = environ.get("NEO4J_CDISC_IMPORT_HOST")
NEO4J_STAGING_BOLT_PORT = environ.get("NEO4J_CDISC_IMPORT_BOLT_PORT")
NEO4J_STAGING_AUTH_USER = environ.get("NEO4J_CDISC_IMPORT_AUTH_USER")
NEO4J_STAGING_AUTH_PASSWORD = environ.get("NEO4J_CDISC_IMPORT_AUTH_PASSWORD")
NEO4J_STAGING_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE")


IMPORT_USERNAME = environ.get("IMPORT_USERNAME", "testuser")
IMPORT_AUTHOR_ID = IMPORT_USERNAME
SIDELOAD_SUFFIX = "_sideload"

# Check SB db environment variables
if not NEO4J_SB_HOST:
    raise ValueError("NEO4J_MDR_HOST environment variable is not set.")
if not NEO4J_SB_BOLT_PORT:
    raise ValueError("NEO4J_MDR_BOLT_PORT environment variable is not set.")
if not NEO4J_SB_AUTH_USER:
    raise ValueError("NEO4J_MDR_AUTH_USER environment variable is not set.")
if not NEO4J_SB_AUTH_PASSWORD:
    raise ValueError("NEO4J_MDR_AUTH_PASSWORD environment variable is not set.")
if not NEO4J_SB_DATABASE:
    raise ValueError("NEO4J_MDR_DATABASE environment variable is not set.")

# Check staging db environment variables
if not NEO4J_STAGING_HOST:
    raise ValueError("NEO4J_CDISC_IMPORT_HOST environment variable is not set.")
if not NEO4J_STAGING_BOLT_PORT:
    raise ValueError("NEO4J_CDISC_IMPORT_BOLT_PORT environment variable is not set.")
if not NEO4J_STAGING_AUTH_USER:
    raise ValueError("NEO4J_CDISC_IMPORT_AUTH_USER environment variable is not set.")
if not NEO4J_STAGING_AUTH_PASSWORD:
    raise ValueError(
        "NEO4J_CDISC_IMPORT_AUTH_PASSWORD environment variable is not set."
    )
if not NEO4J_STAGING_DATABASE:
    raise ValueError("NEO4J_CDISC_IMPORT_DATABASE environment variable is not set.")


BATCH_SIZE = 1000


def get_logger():
    loglevel = environ.get("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {loglevel}, defaulting to INFO")
        numeric_level = logging.INFO
    logging.basicConfig()
    logger = logging.getLogger("CDISC import")
    logger.setLevel(numeric_level)
    return logger


LOGGER = get_logger()


# Database connections and queries
def get_staging_db_driver():
    uri = "{}://{}:{}".format(
        NEO4J_PROTOCOL, NEO4J_STAGING_HOST, NEO4J_STAGING_BOLT_PORT
    )
    return GraphDatabase.driver(
        uri,
        auth=(NEO4J_STAGING_AUTH_USER, NEO4J_STAGING_AUTH_PASSWORD),
        database=NEO4J_STAGING_DATABASE,
        max_connection_lifetime=1800,
        keep_alive=True,
        connection_acquisition_timeout=60.0,
        liveness_check_timeout=30.0,
    )


def get_sb_db_driver():
    uri = "{}://{}:{}".format(NEO4J_PROTOCOL, NEO4J_SB_HOST, NEO4J_SB_BOLT_PORT)
    return GraphDatabase.driver(
        uri,
        auth=(NEO4J_SB_AUTH_USER, NEO4J_SB_AUTH_PASSWORD),
        database=NEO4J_SB_DATABASE,
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


def run_single_query_auto(session, query, parameters=None):
    data = session.run(query, parameters).data()
    return data


def print_stats(stats):
    if stats is None:
        print("No changes were made.")
        return
    print("Stats:")
    print("Attributes updated: ", stats["attrs_updated"])
    print("Attributes created: ", stats["attrs_created"])
    print("Attributes unchanged: ", stats["attrs_unchanged"])
    print("Names updated: ", stats["names_updated"])
    print("Names created: ", stats["names_created"])
    print("Names unchanged: ", stats["names_unchanged"])


# Create indexes in the SB database
def create_indexes(session, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    queries = [
        f"CREATE INDEX catalogue_name{suffix} IF NOT EXISTS FOR (n:CTCatalogue{suffix}) ON (n.name)",
        f"CREATE INDEX cl_root_uid{suffix} IF NOT EXISTS FOR (n:CTCodelistRoot{suffix}) ON (n.uid)",
        f"CREATE INDEX ct_pack_uid{suffix} IF NOT EXISTS FOR (n:CTPackage{suffix}) ON (n.uid)",
        f"CREATE INDEX ct_pack_name{suffix} IF NOT EXISTS FOR (n:CTPackage{suffix}) ON (n.name)",
        f"CREATE INDEX package_cl_uid{suffix} IF NOT EXISTS FOR (n:CTPackageCodelist{suffix}) ON (n.uid)",
        f"CREATE INDEX package_term_uid{suffix} IF NOT EXISTS FOR (n:CTPackageTerm{suffix}) ON (n.uid)",
        f"CREATE INDEX term_root_uid{suffix} IF NOT EXISTS FOR (n:CTTermRoot{suffix}) ON (n.uid)",
        "CREATE INDEX lib_name IF NOT EXISTS FOR (n:Library) ON (n.name)",
        f"CREATE INDEX term_submval{suffix} IF NOT EXISTS FOR (n:CTCodelistTerm{suffix}) ON (n.submission_value)",
    ]
    for query in queries:
        run_single_query(session, query)


# check if import user exists in SB database
def check_sb_import_exists(sb_db_driver):
    query = """
        MATCH (u:User {username: $username})
        RETURN u
        """
    result = run_single_query_auto(
        sb_db_driver.session(),
        query,
        parameters={"username": IMPORT_USERNAME},
    )
    return len(result) > 0


# get import user id from SB database
def get_import_user_id(sb_db_driver):
    query = """
        MATCH (u:User {username: $username})
        RETURN u.user_id AS user_id
        """
    result = run_single_query_auto(
        sb_db_driver.session(),
        query,
        parameters={"username": IMPORT_USERNAME},
    )
    if len(result) == 0:
        raise ValueError(f"import user '{IMPORT_USERNAME}' not found in SB database")
    return result[0]["user_id"]


###### Libraries, catalogues and packages
def merge_library(session, name, editable):
    query = """
        MERGE (l:Library {name: $name})
        SET l.is_editable = $editable
        RETURN l
        """
    run_single_query(session, query, parameters={"name": name, "editable": editable})


def merge_catalogue(session, library_name, catalogue_name, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    query = f"""
        MATCH (l:Library {{name: $library_name}})
        MERGE (l)-[:CONTAINS_CATALOGUE]->(cat:CTCatalogue{suffix} {{name: $catalogue_name}})
        RETURN cat
        """
    run_single_query(
        session,
        query,
        parameters={"library_name": library_name, "catalogue_name": catalogue_name},
    )


def merge_package(session, package, author_id, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    query = f"""
        MATCH (cat:CTCatalogue{suffix} {{name: $package.catalogue_name}})
        MERGE (cat)-[:CONTAINS_PACKAGE]->(pak:CTPackage{suffix} {{uid: $package.uid, name: $package.name}})
        ON CREATE SET pak.import_date = datetime(), pak.author_id = $author_id, pak.effective_date = datetime($package.effectiveDate)
        WITH pak
        MATCH (prevpak:CTPackage{suffix} {{name: $package.prior_version_name}})
        MERGE (pak)<-[:NEXT_PACKAGE]-(prevpak)
        RETURN pak
        """
    run_single_query(
        session,
        query,
        parameters={"package": package, "author_id": author_id},
    )


def fetch_catalogues_and_packages(session):
    query = """
        MATCH (cat:RawCatalogue)
        OPTIONAL MATCH (cat)-[:HAS_PRIOR_VERSION]-(prev)
        RETURN *
        """
    cats = set()
    packages = []
    for record in run_single_query(session, query):
        pack = record["cat"]
        if record["prev"] is not None:
            pack["prior_version_name"] = record["prev"]["name"]
        else:
            pack["prior_version_name"] = None
        packages.append(pack)
        catalogue = pack["name"][0:-11]
        pack["catalogue_name"] = catalogue
        pack["uid"] = pack["name"].replace(" ", "__")
        cats.add(catalogue)
    return cats, packages


def merge_libraries_catalogues_packages(
    staging_db_driver, sb_db_driver, sideload_data: bool = False
):
    with staging_db_driver.session() as staging_session, sb_db_driver.session() as sb_session:
        # CDISC Library
        merge_library(sb_session, "CDISC", False)

        # Catalogues and Packages
        cats, packages = fetch_catalogues_and_packages(staging_session)
        for cat in cats:
            merge_catalogue(sb_session, "CDISC", cat, sideload_data)
        for pack in packages:
            merge_package(sb_session, pack, IMPORT_AUTHOR_ID, sideload_data)


###### Codelists


def fetch_versioned_codelists(session):
    query = """
        MATCH (vcl:VersionedCodelist)-[hv:HAS_VERSION]->(clv:CodelistVersion)-[:FROM_PACKAGE]->(gclp:GroupedCodelistProperties)<-[:HAS_GROUPED_PROPERTIES]-(gcp:GroupedCodelist)-[:SOURCE_CODELIST_DEF]->(rcl:RawCodelist)<-[:HAS_RAW_CODELIST]-(cat:RawCatalogue)
        OPTIONAL MATCH (vcl)-[:PAIRED_WITH_CODES]->(paired_code_cl:VersionedCodelist)
        WITH vcl, hv, clv, collect(cat) as vcats, paired_code_cl.conceptId as paired_codes ORDER BY hv.version
        WITH vcl, paired_codes, collect(properties(hv)) as hvs, collect(clv) as clvs, collect(vcats) as cats
        CALL (vcl) {
            OPTIONAL MATCH (vcl)-[ht:HAS_TERM]->(:VersionedTerm)
            RETURN collect(DISTINCT ht.submissionValue) AS term_submvals
        }
        RETURN *
        """
    return run_single_query(session, query)


def is_int_like(value):
    """Return True if value is an integer, or a string representation of one (e.g. "1")."""
    if value is None:
        return False
    try:
        int(str(value).strip())
        return True
    except (TypeError, ValueError):
        return False


def parse_ordinal_value(submission_value):
    """
    Convert a term's submission value to an ordinal value.
    Returns None if the submission value is not an integer (e.g. "UNKNOWN", "N/A", or any other
    non-numeric string), in which case no ordinal value should be set for that term.
    """
    if not is_int_like(submission_value):
        return None
    return float(int(str(submission_value).strip()))


def determine_codelist_is_ordinal(name, term_submvals):
    """
    A codelist should be treated as ordinal if its name contains "STRESC" and at least one of
    its terms has an integer submission value (or a string version of one, e.g. "1").
    """
    if not name or "STRESC" not in name.upper():
        return False
    return any(is_int_like(submval) for submval in (term_submvals or []))


def merge_codelist_roots(session, codelists, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    # create the codelist root, and the CTPackageCodelists
    query = f"""
        MATCH (lib:Library {{name: "CDISC"}})
        UNWIND $codelists as codelist
        CALL (codelist, lib) {{
            MERGE (clr:CTCodelistRoot{suffix} {{uid: codelist.vcl.conceptId}})
            MERGE (lib)-[:CONTAINS_CODELIST]->(clr)
            MERGE (clr)-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot{suffix})
            MERGE (clr)-[:HAS_ATTRIBUTES_ROOT]->(clar:CTCodelistAttributesRoot{suffix})
            WITH clr, codelist
            UNWIND codelist.cats as vcat
                UNWIND vcat as cat
                MATCH (ctcat:CTCatalogue{suffix} {{name: left(cat.name, size(cat.name)-11)}})
                MERGE (clr)<-[:HAS_CODELIST]-(ctcat)
            WITH clr, codelist
            UNWIND codelist.cats as vcat
                UNWIND vcat as cat
                MATCH (ctpack:CTPackage{suffix} {{name: cat.name}})
                MERGE (ctpack)-[:CONTAINS_CODELIST]-(:CTPackageCodelist{suffix} {{uid: cat.uid + '_' + codelist.vcl.conceptId}})
        }}
        """
    run_single_query(session, query, parameters={"codelists": codelists})


def link_code_name_codelist_pairs(session, codelists, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    codelists_to_link = [cl for cl in codelists if cl["paired_codes"] is not None]
    query = f"""
        UNWIND $codelist_pairs as pair
        CALL (pair) {{
            MATCH (names:CTCodelistRoot{suffix} {{uid: pair.vcl.conceptId}})
            MATCH (codes:CTCodelistRoot{suffix} {{uid: pair.paired_codes}})
            MERGE (names)-[:PAIRED_CODE_CODELIST]->(codes)
        }}
        """
    run_single_query(session, query, parameters={"codelist_pairs": codelists_to_link})


def merge_codelist_versions(session, codelist, stats=None, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    existing_query = f"""
        MATCH (clar:CTCodelistAttributesRoot{suffix})<-[:HAS_ATTRIBUTES_ROOT]-(clr:CTCodelistRoot{suffix} {{uid: $codelist.vcl.conceptId}})
            -[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot{suffix})
        WITH clr, clar, clnr, 
            COLLECT {{ 
                MATCH (clar)-[hv:HAS_VERSION]-(clav:CTCodelistAttributesValue{suffix})<-[:CONTAINS_ATTRIBUTES]-(ctpcl)
                WITH clav, hv, collect(ctpcl.uid) as pcl_uids ORDER BY hv.start_date 
                WITH clav{{.*, pcl_uids, start_date: hv.start_date, end_date: hv.end_date, version: hv.version}} AS row
                RETURN row
            }} AS avs,
            COLLECT {{
                MATCH (clnr)-[hv:HAS_VERSION]-(clnv:CTCodelistNameValue{suffix})
                WITH clnv, hv ORDER BY hv.start_date
                WITH clnv{{.*, start_date: hv.start_date, end_date: hv.end_date, version: hv.version}} AS row
                RETURN row
            }} AS nvs
        RETURN *
    """

    create_attrs_query = f"""
    MATCH (clar:CTCodelistAttributesRoot{suffix})<-[:HAS_ATTRIBUTES_ROOT]-(clr:CTCodelistRoot{suffix} {{uid: $codelist_uid}})
    WITH clr, clar
    CREATE (clar)-[:HAS_VERSION {{start_date: datetime($attr.start_date), end_date: datetime($attr.end_date), version: $attr.version, status: "Final", author_id: $author_id}}]->(clav:CTCodelistAttributesValue{suffix} {{name: $attr.value.name, preferred_term: $attr.value.preferred_term, submission_value: $attr.value.submission_value, definition: $attr.value.definition, concept_id: $attr.value.concept_id, extensible: $attr.value.extensible, synonyms: $attr.value.synonyms}})
    WITH clar, clav
    MATCH (ctpcl:CTPackageCodelist{suffix}) WHERE ctpcl.uid IN $attr.package_codelist_uids
    MERGE (clav)<-[:CONTAINS_ATTRIBUTES]-(ctpcl)
    WITH clar, clav
    CALL (clar, clav) {{
        WITH clar, clav WHERE $attr.end_date IS NULL
        MERGE (clar)-[:LATEST]->(clav)
        MERGE (clar)-[:LATEST_FINAL]->(clav)
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    update_attr_end_date_query = f"""
    MATCH (clar:CTCodelistAttributesRoot{suffix})<-[:HAS_ATTRIBUTES_ROOT]-(clr:CTCodelistRoot{suffix} {{uid: $codelist_uid}})-[:HAS_VERSION {{start_date: datetime($attr.start_date), version: $attr.version}}]->(clav:CTCodelistAttributesValue{suffix})
    SET clav.end_date = datetime($attr.end_date)
    WITH clar, clav
    CALL (clar, clav) {{
        WITH clar, clav WHERE $attr.end_date IS NOT NULL
        MATCH (clar)-[l:LATEST]->(clav)
        DELETE l
        WITH clar, clav
        MATCH (clar)-[lf:LATEST_FINAL]->(clav)
        DELETE lf
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    create_name_query = f"""
    MATCH (clnr:CTCodelistNameRoot{suffix})<-[:HAS_NAME_ROOT]-(clr:CTCodelistRoot{suffix} {{uid: $codelist_uid}})
    WITH clnr
    CREATE (clnr)-[:HAS_VERSION {{start_date: datetime($name.start_date), end_date: datetime($name.end_date), version: $name.version, status: "Final", author_id: $author_id}}]->(clnv:CTCodelistNameValue{suffix} {{name: $name.value.name, name_sentence_case: $name.value.name_sentence_case, is_ordinal: $name.value.is_ordinal, codelist_type: $name.value.codelist_type}})
    WITH clnr, clnv
    CALL (clnr, clnv) {{
        WITH clnr, clnv WHERE $name.end_date IS NULL
        MERGE (clnr)-[:LATEST]->(clnv)
        MERGE (clnr)-[:LATEST_FINAL]->(clnv)
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    update_name_end_date_query = f"""
    MATCH (clnr:CTCodelistNameRoot{suffix})<-[:HAS_NAME_ROOT]-(clr:CTCodelistRoot{suffix} {{uid: $codelist_uid}})-[:HAS_VERSION {{start_date: datetime($name.start_date), version: $name.version}}]->(clnv:CTCodelistNameValue{suffix})
    SET clnv.end_date = datetime($name.end_date)
    WITH clnr, clnv
    CALL (clnr, clnv) {{
        WITH clnr, clnv WHERE $name.end_date IS NOT NULL
        MATCH (clnr)-[l:LATEST]->(clnv)
        DELETE l
        WITH clnr, clnv
        MATCH (clnr)-[lf:LATEST_FINAL]->(clnv)
        DELETE lf
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    if stats is None:
        stats = {
            "attrs_updated": 0,
            "attrs_created": 0,
            "attrs_unchanged": 0,
            "names_updated": 0,
            "names_created": 0,
            "names_unchanged": 0,
        }
    # <-[:CONTAINS_ATTRIBUTES]-(ctpcl:CTPackageCodelist)-[:CONTAINS_CODELIST]-(ctp:CTPackage)
    existing_versions = run_single_query(
        session, existing_query, parameters={"codelist": codelist}
    )
    names_to_merge, attrs_to_merge = extract_cl_names_and_attributes(codelist)
    for attr in attrs_to_merge:
        build_ct_package_codelist_uids(codelist, attr)
        # neo4j doesn't like sets, convert to a list
        attr["value"]["synonyms"] = list(attr["value"]["synonyms"])

        if len(existing_versions) > 0 and len(existing_versions[0]["avs"]) > 0:
            # There were already some versions of these attributes before the import started.
            # We need to make sure to update these to match the new data.
            start_date = datetime.fromisoformat(attr["start_date"]).replace(
                tzinfo=timezone.utc
            )
            end_date = (
                datetime.fromisoformat(attr.get("end_date")).replace(
                    tzinfo=timezone.utc
                )
                if attr.get("end_date") is not None
                else None
            )
            matching = find_item_with_matching_start_date(
                start_date, existing_versions[0]["avs"]
            )
            if matching is not None:
                if matching["end_date"] == end_date:
                    # The version we are adding already exists, and the start and end dates are the same, so we are done
                    stats["attrs_unchanged"] += 1
                else:
                    # a version with the same start date but different end date exists.
                    # this means that this term has been updated in the standards data, and we need to retire the term also in the SB db.
                    # Update the end date, and if the end date is not null (should normally be the case here), remove any LATEST and LATEST_FINAL relationships
                    LOGGER.debug("attr, update end date! %s", matching)
                    run_single_query(
                        session,
                        update_attr_end_date_query,
                        parameters={
                            "codelist_uid": codelist["vcl"]["conceptId"],
                            "attr": attr,
                        },
                    )
                    stats["attrs_updated"] += 1
                # check if the properties are the same, if not warn. Or just update them?
                # check if linked catalogues are the same, add any that are missing
            else:
                # a version with the same start date does not exist, this means we are adding a new version.
                # Find the previous version and retire it, and remove any LATEST and LATEST_FINAL relationships.
                # This will most of the time be handled by the previous block, but if we are importing a subset of packages
                # this might not have been done yet.
                LOGGER.debug(
                    "attr find the previous version and update end date, then create the new version"
                )
                existing_active = find_item_active_at_date(
                    start_date, existing_versions[0]["avs"]
                )
                if existing_active is not None:
                    LOGGER.debug("Retire this attr: %s", existing_active)
                    run_single_query(
                        session,
                        update_attr_end_date_query,
                        parameters={
                            "codelist_uid": existing_active["concept_id"],
                            "attr": existing_active,
                        },
                    )
                    stats["attrs_updated"] += 1
                # and remove any LATEST and LATEST_FINAL relationships from it
                # run_single_query(session, retire_previous_name_query, parameters={"codelist": codelist, "name": name})
                run_single_query(
                    session,
                    create_attrs_query,
                    parameters={
                        "codelist_uid": codelist["vcl"]["conceptId"],
                        "attr": attr,
                        "author_id": IMPORT_AUTHOR_ID,
                    },
                )
                stats["attrs_created"] += 1
        else:
            LOGGER.debug("attr not found, just create the new version")
            run_single_query(
                session,
                create_attrs_query,
                parameters={
                    "codelist_uid": codelist["vcl"]["conceptId"],
                    "attr": attr,
                    "author_id": IMPORT_AUTHOR_ID,
                },
            )
            stats["attrs_created"] += 1
            # raise ValueError("stop")

    for name in names_to_merge:
        if len(existing_versions) > 0 and len(existing_versions[0]["nvs"]) > 0:
            # There were already some versions of this name before the import started.
            # We need to make sure to update these to match the new data.
            start_date = datetime.fromisoformat(name["start_date"]).replace(
                tzinfo=timezone.utc
            )
            end_date = (
                datetime.fromisoformat(name.get("end_date")).replace(
                    tzinfo=timezone.utc
                )
                if name.get("end_date") is not None
                else None
            )
            matching = find_item_with_matching_start_date(
                start_date, existing_versions[0]["nvs"]
            )
            if matching is not None:
                if matching["end_date"] == end_date:
                    # The version we are adding already exists, and the start and end dates are the same, so we are done
                    stats["names_unchanged"] += 1
                else:
                    # a version with the same start date but different end date exists.
                    # this means that this term has been updated in the standards data, and we need to retire the term also in the SB db.
                    # Update the end date, and if the end date is not null (should normally be the case here), remove any LATEST and LATEST_FINAL relationships
                    LOGGER.debug("name, update end date: %s", matching)
                    run_single_query(
                        session,
                        update_name_end_date_query,
                        parameters={
                            "codelist_uid": codelist["vcl"]["conceptId"],
                            "name": name,
                        },
                    )
                    stats["names_updated"] += 1
                # check if the properties are the same, if not warn. Or just update them?
            else:
                # a version with the same start date does not exist, this means we are adding a new version.
                # Find the previous version and retire it, and remove any LATEST and LATEST_FINAL relationships.
                # This will most of the time be handled by the previous block, but if we are importing a subset of packages
                # this might not have been done yet.
                LOGGER.debug(
                    "name find the previous version and update end date, then create the new version"
                )
                existing_active = find_item_active_at_date(
                    start_date, existing_versions[0]["nvs"]
                )
                if existing_active is not None:
                    LOGGER.debug("Retire this name: %s", existing_active)
                    run_single_query(
                        session,
                        update_name_end_date_query,
                        parameters={
                            "codelist_uid": existing_active["concept_id"],
                            "name": existing_active,
                        },
                    )
                    stats["names_updated"] += 1
                # and remove any LATEST and LATEST_FINAL relationships from it
                # run_single_query(session, retire_previous_name_query, parameters={"codelist": codelist, "name": name})
                run_single_query(
                    session,
                    create_name_query,
                    parameters={
                        "codelist_uid": codelist["vcl"]["conceptId"],
                        "name": name,
                        "author_id": IMPORT_AUTHOR_ID,
                    },
                )
                stats["names_created"] += 1
        else:
            # There are no existing versions yet, just create the new versions
            LOGGER.debug("name not found, just create the new version")
            run_single_query(
                session,
                create_name_query,
                parameters={
                    "codelist_uid": codelist["vcl"]["conceptId"],
                    "name": name,
                    "author_id": IMPORT_AUTHOR_ID,
                },
            )
            stats["names_created"] += 1
            # raise ValueError("stop")

    return stats


def build_ct_package_codelist_uids(codelist, attr):
    uids = [
        package_name.replace(" ", "__") + "_" + codelist["vcl"]["conceptId"]
        for package_name in attr["catalogues"]
    ]
    del attr["catalogues"]
    attr["package_codelist_uids"] = uids


def find_item_with_matching_start_date(start_date, items):
    for item in items:
        if item["start_date"] == start_date:
            return item
    LOGGER.debug("not found!, %s, %s", start_date, items)
    return None


def find_item_active_at_date(start_date, items):
    for item in items:
        if item["start_date"] < start_date and item["end_date"] is None:
            return item
    return None


def increment_version(new_version, existing_versions):
    prev_version_nbr = existing_versions[-1]["version"]
    major = int(prev_version_nbr.split(".")[0])
    new_version_nbr = "{}.0".format(major + 1)
    new_version["version"] = new_version_nbr


def compare_cl_attributes(new, old):
    return (
        old["name"] == new["name"]
        and old["preferred_term"] == new["preferred_term"]
        and old["submission_value"] == new["submission_value"]
        and old["definition"] == new["definition"]
        and old["concept_id"] == new["concept_id"]
        and old["extensible"] == new["extensible"]
        and set(old["synonyms"]) == set(new["synonyms"])
    )


def compare_cl_names(new, old):
    return (
        old["name"] == new["name"]
        and old["name_sentence_case"] == new["name_sentence_case"]
        and old.get("is_ordinal", False) == new.get("is_ordinal", False)
        and old.get("codelist_type", "Standard") == new.get("codelist_type", "Standard")
    )


def append_version(new, existing, compare_func):
    if len(existing) == 0:
        existing.append(new)
    else:
        prev_val = existing[-1]["value"]
        if compare_func(new["value"], prev_val):
            existing[-1]["end_date"] = new.get("end_date")
            if "catalogues" in new:
                existing[-1]["catalogues"].update(new["catalogues"])
        else:
            # New version, increment major version
            increment_version(new, existing)
            existing.append(new)


def extract_cl_names_and_attributes(codelist):
    names = []
    attributes = []
    term_submvals = codelist.get("term_submvals", [])
    for hv, clv, cats in zip(codelist["hvs"], codelist["clvs"], codelist["cats"]):

        name = clv["name"]
        name_sentence_case = get_sentence_case_string(name)
        is_ordinal = determine_codelist_is_ordinal(name, term_submvals)
        name_value = {
            "name": name,
            "name_sentence_case": name_sentence_case,
            "is_ordinal": is_ordinal,
            "codelist_type": "Standard",
        }
        name_version = {
            "value": name_value,
            "start_date": hv["start_date"],
            "end_date": hv.get("end_date"),
            "version": "1.0",
        }

        append_version(name_version, names, compare_cl_names)
        catalogues = [cat["name"] for cat in cats]
        synonyms = clv["synonyms"]
        concept_id = codelist["vcl"]["conceptId"]
        extensible = clv.get("extensible", False)
        definition = clv["definition"]
        submval = clv["submissionValue"]
        attributes_value = {
            "name": name,
            "synonyms": synonyms,
            "concept_id": concept_id,
            "definition": definition,
            "preferred_term": name,
            "submission_value": submval,
            "extensible": extensible,
        }
        attributes_version = {
            "value": attributes_value,
            "start_date": hv["start_date"],
            "end_date": hv.get("end_date"),
            "version": "1.0",
            "catalogues": set(catalogues),
        }

        append_version(attributes_version, attributes, compare_cl_attributes)

    return names, attributes


def make_clean_package_names(codelists):
    for codelist in codelists:
        for cat in codelist["cats"]:
            for vcat in cat:
                vcat["uid"] = vcat["name"].replace(" ", "__")


def merge_codelists(staging_db_driver, sb_db_driver, sideload_data: bool = False):
    with staging_db_driver.session() as staging_session, sb_db_driver.session() as sb_session:
        # Codelists
        codelists = fetch_versioned_codelists(staging_session)
        make_clean_package_names(codelists)
        merge_codelist_roots(sb_session, codelists, sideload_data)
        link_code_name_codelist_pairs(sb_session, codelists, sideload_data)
        stats = None
        for codelist in codelists:
            stats = merge_codelist_versions(sb_session, codelist, stats, sideload_data)
        print_stats(stats)


###### Terms
def count_versioned_terms(session):
    query = """MATCH (vt:VersionedTerm) RETURN count(vt) as cnt"""
    result = run_single_query(session, query)
    return result[0]["cnt"]


def fetch_versioned_terms(session, skip=0, limit=100):
    query = """
    MATCH (vt:VersionedTerm) WITH vt ORDER BY vt.conceptId SKIP $skip LIMIT $limit
    MATCH (vt)-[hv:HAS_VERSION]->(tv:TermVersion)<-[:SPONSOR_NAME_FOR]-(sn:SponsorName)
    WITH *, COLLECT { 
        MATCH (tv)-[:FROM_PACKAGE]->(:GroupedTermProperties)<-[:HAS_GROUPED_PROPERTIES]-
              (gt:GroupedTerm)-[:SOURCE_TERM_DEF]->(rt:RawTerm)<-[:HAS_RAW_TERM]-(rcl:RawCodelist)<-[:HAS_RAW_CODELIST]-(cat:RawCatalogue) 
        MATCH (gt)-[ht:HAS_TERM]-(:GroupedCodelist)
        RETURN {codelist: rcl.conceptId, catalogue: cat.name, submval: ht.submissionValue} } as package_data ORDER BY hv.version
    WITH properties(vt) as term, collect(properties(hv)) as hasversions, collect(properties(tv)) as values, collect(sn.name) as sponsor_names, collect(package_data) as packages
    RETURN *"""
    return run_single_query(session, query, parameters={"skip": skip, "limit": limit})


def merge_term_roots(session, terms, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    # Query 1: create the term root nodes and link to library
    # Split from query 2 to avoid Eager operator caused by read/write conflict
    # on CONTAINS_TERM relationship type (lib->tr read vs packcl->pt write)
    roots_query = f"""
        MATCH (lib:Library {{name: "CDISC"}})
        UNWIND $terms as term
        CALL (term, lib) {{
            MERGE (tr:CTTermRoot{suffix} {{uid: term.term.conceptId}})
            MERGE (lib)-[:CONTAINS_TERM]->(tr)
            MERGE (tr)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot{suffix})
            MERGE (tr)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot{suffix})
        }}
        """
    run_single_query(session, roots_query, parameters={"terms": terms})

    # Query 2: create CTPackageTerms and link to codelists.
    # Flatten list-of-lists-of-packages into a single deduped row list on the
    # Python side so Neo4j plans a single UNWIND instead of three nested ones
    # — the nested form blew through dbms.memory.transaction.total.max.
    flat_rows = flatten_term_package_rows(terms)
    if not flat_rows:
        return
    packages_query = f"""
        UNWIND $rows as row
        CALL (row) {{
            MATCH (tr:CTTermRoot{suffix} {{uid: row.term_uid}})
            MATCH (packcl:CTPackageCodelist{suffix} {{uid: row.packcl_uid}})
            MERGE (pt:CTPackageTerm{suffix} {{uid: row.pt_uid}})
            MERGE (packcl)-[:CONTAINS_TERM]->(pt)
            MERGE (tr)<-[:HAS_TERM_ROOT]-(ctpt:CTCodelistTerm{suffix} {{submission_value: row.submval}})
            MERGE (pt)-[:CONTAINS_SUBMISSION_VALUE]->(ctpt)
        }}
        """
    run_single_query(session, packages_query, parameters={"rows": flat_rows})


def flatten_term_package_rows(terms):
    seen = set()
    rows = []
    for term in terms:
        term_uid = term["term"]["conceptId"]
        for packages in term["packages"]:
            for pack in packages:
                catalogue = pack["catalogue"]
                codelist = pack["codelist"]
                submval = pack["submval"]
                key = (term_uid, catalogue, codelist, submval)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "term_uid": term_uid,
                        "packcl_uid": f"{catalogue}_{codelist}",
                        "pt_uid": f"{catalogue}_{term_uid}",
                        "submval": submval,
                    }
                )
    return rows


def make_clean_term_package_names(terms):
    for term in terms:
        for packages in term["packages"]:
            for pack in packages:
                pack["catalogue"] = pack["catalogue"].replace(" ", "__")


def merge_term_versions(session, term, stats=None, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    existing_query = f"""
        MATCH (tar:CTTermAttributesRoot{suffix})<-[:HAS_ATTRIBUTES_ROOT]-(tr:CTTermRoot{suffix} {{uid: $term.term.conceptId}})-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot{suffix})
        WITH tr, tar, tnr, 
            COLLECT {{ 
                MATCH (tar)-[hv:HAS_VERSION]-(tav:CTTermAttributesValue{suffix})<-[:CONTAINS_ATTRIBUTES]-(ctpt)
                WITH tav, hv, collect(ctpt.uid) as pt_uids ORDER BY hv.start_date 
                WITH tav{{.*, pt_uids, start_date: hv.start_date, end_date: hv.end_date, version: hv.version}} AS row
                RETURN row
            }} AS avs,
            COLLECT {{
                MATCH (tnr)-[hv:HAS_VERSION]-(tnv:CTTermNameValue{suffix})
                WITH tnv, hv ORDER BY hv.start_date
                WITH tnv{{.*, start_date: hv.start_date, end_date: hv.end_date, version: hv.version}} AS row
                RETURN row
            }} AS nvs
        RETURN *
    """

    create_attrs_query = f"""
    MATCH (tar:CTTermAttributesRoot{suffix})<-[:HAS_ATTRIBUTES_ROOT]-(tr:CTTermRoot{suffix} {{uid: $term_uid}})
    WITH tr, tar
    CREATE (tar)-[:HAS_VERSION {{start_date: datetime($attr.start_date), end_date: datetime($attr.end_date), version: $attr.version, status: "Final", author_id: $author_id}}]->(tav:CTTermAttributesValue{suffix} {{preferred_term: $attr.value.preferred_term, definition: $attr.value.definition, concept_id: $attr.value.concept_id, synonyms: $attr.value.synonyms}})
    WITH tar, tav
    MATCH (ctpt:CTPackageTerm{suffix}) WHERE ctpt.uid IN $attr.package_term_uids
    MERGE (tav)<-[:CONTAINS_ATTRIBUTES]-(ctpt)
    WITH tar, tav
    CALL (tar, tav) {{
        WITH tar, tav WHERE $attr.end_date IS NULL
        MERGE (tar)-[:LATEST]->(tav)
        MERGE (tar)-[:LATEST_FINAL]->(tav)
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    update_attr_end_date_query = f"""
    MATCH (tar:CTTermAttributesRoot{suffix})<-[:HAS_ATTRIBUTES_ROOT]-(tr:CTTermRoot{suffix} {{uid: $term_uid}})-[:HAS_VERSION {{start_date: datetime($attr.start_date), version: $attr.version}}]->(tav:CTTermAttributesValue{suffix})
    SET tav.end_date = datetime($attr.end_date)
    WITH tar, tav
    CALL (tar, tav) {{
        WITH tar, tav WHERE $attr.end_date IS NOT NULL
        MATCH (tar)-[l:LATEST]->(tav)
        DELETE l
        WITH tar, tav
        MATCH (tar)-[lf:LATEST_FINAL]->(tav)
        DELETE lf
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    create_name_query = f"""
    MATCH (tnr:CTTermNameRoot{suffix})<-[:HAS_NAME_ROOT]-(tr:CTTermRoot{suffix} {{uid: $term_uid}})
    WITH tnr
    CREATE (tnr)-[:HAS_VERSION {{start_date: datetime($name.start_date), end_date: datetime($name.end_date), version: $name.version, status: "Final", author_id: $author_id}}]->(tnv:CTTermNameValue{suffix} {{name: $name.value.name, name_sentence_case: $name.value.name_sentence_case}})
    WITH tnr, tnv
    CALL (tnr, tnv) {{
        WITH tnr, tnv WHERE $name.end_date IS NULL
        MERGE (tnr)-[:LATEST]->(tnv)
        MERGE (tnr)-[:LATEST_FINAL]->(tnv)
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    update_name_end_date_query = f"""
    MATCH (tnr:CTTermNameRoot{suffix})<-[:HAS_NAME_ROOT]-(tr:CTTermRoot{suffix} {{uid: $term_uid}})-[:HAS_VERSION {{start_date: datetime($name.start_date), version: $name.version}}]->(tnv:CTTermNameValue{suffix})
    SET tnv.end_date = datetime($name.end_date)
    WITH tnr, tnv
    CALL (tnr, tnv) {{
        WITH tnr, tnv WHERE $name.end_date IS NOT NULL
        MATCH (tnr)-[l:LATEST]->(tnv)
        DELETE l
        WITH tnr, tnv
        MATCH (tnr)-[lf:LATEST_FINAL]->(tnv)
        DELETE lf
        RETURN NULL as dummy
    }}
    RETURN NULL as dummy
    """

    # <-[:CONTAINS_ATTRIBUTES]-(ctpcl:CTPackageCodelist)-[:CONTAINS_CODELIST]-(ctp:CTPackage)
    existing_versions = run_single_query(
        session, existing_query, parameters={"term": term}
    )
    names_to_merge, attrs_to_merge = extract_term_names_and_attributes(term)
    if stats is None:
        stats = {
            "attrs_updated": 0,
            "attrs_created": 0,
            "attrs_unchanged": 0,
            "names_updated": 0,
            "names_created": 0,
            "names_unchanged": 0,
        }

    for attr in attrs_to_merge:
        build_ct_package_term_uids(term, attr)
        # neo4j doesn't like sets, convert to a list
        attr["value"]["synonyms"] = list(attr["value"]["synonyms"])

        if len(existing_versions) > 0 and len(existing_versions[0]["avs"]) > 0:
            # There were already some versions of these attributes before the import started.
            # We need to make sure to update these to match the new data.
            start_date = datetime.fromisoformat(attr["start_date"]).replace(
                tzinfo=timezone.utc
            )
            end_date = (
                datetime.fromisoformat(attr.get("end_date")).replace(
                    tzinfo=timezone.utc
                )
                if attr.get("end_date") is not None
                else None
            )
            matching = find_item_with_matching_start_date(
                start_date, existing_versions[0]["avs"]
            )
            if matching is not None:
                if matching["end_date"] == end_date:
                    # The version we are adding already exists, and the start and end dates are the same, so we are done
                    stats["attrs_unchanged"] += 1
                else:
                    # a version with the same start date but different end date exists.
                    # this means that this term has been updated in the standards data, and we need to retire the term also in the SB db.
                    # Update the end date, and if the end date is not null (should normally be the case here), remove any LATEST and LATEST_FINAL relationships
                    LOGGER.debug("attr, update end date: %s", matching)
                    run_single_query(
                        session,
                        update_attr_end_date_query,
                        parameters={
                            "term_uid": term["term"]["conceptId"],
                            "attr": attr,
                        },
                    )
                # check if the properties are the same, if not warn. Or just update them?
                # check if linked catalogues are the same, add any that are missing
            else:
                # a version with the same start date does not exist, this means we are adding a new version.
                # Find the previous version and retire it, and remove any LATEST and LATEST_FINAL relationships.
                # This will most of the time be handled by the previous block, but if we are importing a subset of packages
                # this might not have been done yet.
                LOGGER.debug(
                    "attr find the previous version and update end date, then create the new version"
                )
                existing_active = find_item_active_at_date(
                    start_date, existing_versions[0]["avs"]
                )
                if existing_active is not None:
                    LOGGER.debug("Retire this attr: %s", existing_active)
                    run_single_query(
                        session,
                        update_attr_end_date_query,
                        parameters={
                            "term_uid": existing_active["concept_id"],
                            "attr": existing_active,
                        },
                    )
                    stats["attrs_updated"] += 1
                # and remove any LATEST and LATEST_FINAL relationships from it
                # run_single_query(session, retire_previous_name_query, parameters={"codelist": codelist, "name": name})
                run_single_query(
                    session,
                    create_attrs_query,
                    parameters={
                        "term_uid": term["term"]["conceptId"],
                        "attr": attr,
                        "author_id": IMPORT_AUTHOR_ID,
                    },
                )
                stats["attrs_created"] += 1
        else:
            stats["attrs_created"] += 1
            run_single_query(
                session,
                create_attrs_query,
                parameters={
                    "term_uid": term["term"]["conceptId"],
                    "attr": attr,
                    "author_id": IMPORT_AUTHOR_ID,
                },
            )
            # raise ValueError("stop")

    for name in names_to_merge:
        if len(existing_versions) > 0 and len(existing_versions[0]["nvs"]) > 0:
            # There were already some versions of this name before the import started.
            # We need to make sure to update these to match the new data.
            start_date = datetime.fromisoformat(name["start_date"]).replace(
                tzinfo=timezone.utc
            )
            end_date = (
                datetime.fromisoformat(name.get("end_date")).replace(
                    tzinfo=timezone.utc
                )
                if name.get("end_date") is not None
                else None
            )
            matching = find_item_with_matching_start_date(
                start_date, existing_versions[0]["nvs"]
            )
            if matching is not None:
                if matching["end_date"] == end_date:
                    # The version we are adding already exists, and the start and end dates are the same, so we are done
                    stats["names_unchanged"] += 1
                else:
                    # a version with the same start date but different end date exists.
                    # this means that this term has been updated in the standards data, and we need to retire the term also in the SB db.
                    # Update the end date, and if the end date is not null (should normally be the case here), remove any LATEST and LATEST_FINAL relationships
                    stats["names_updated"] += 1
                    LOGGER.debug("name, update end date: %s", matching)
                    run_single_query(
                        session,
                        update_name_end_date_query,
                        parameters={
                            "term_uid": term["term"]["conceptId"],
                            "name": name,
                        },
                    )
                # check if the properties are the same, if not warn. Or just update them?
            else:
                # a version with the same start date does not exist, this means we are adding a new version.
                # Find the previous version and retire it, and remove any LATEST and LATEST_FINAL relationships.
                # This will most of the time be handled by the previous block, but if we are importing a subset of packages
                # this might not have been done yet.
                LOGGER.debug(
                    "name find the previous version and update end date, then create the new version"
                )
                existing_active = find_item_active_at_date(
                    start_date, existing_versions[0]["nvs"]
                )
                if existing_active is not None:
                    LOGGER.debug("Retire this name: %s", existing_active)
                    run_single_query(
                        session,
                        update_name_end_date_query,
                        parameters={
                            "term_uid": existing_active["concept_id"],
                            "name": existing_active,
                        },
                    )
                    stats["names_updated"] += 1
                # and remove any LATEST and LATEST_FINAL relationships from it
                # run_single_query(session, retire_previous_name_query, parameters={"codelist": codelist, "name": name})
                run_single_query(
                    session,
                    create_name_query,
                    parameters={
                        "term_uid": term["term"]["conceptId"],
                        "name": name,
                        "author_id": IMPORT_AUTHOR_ID,
                    },
                )
                stats["names_created"] += 1
        else:
            # There are no existing versions yet, just create the new versions
            stats["names_created"] += 1
            run_single_query(
                session,
                create_name_query,
                parameters={
                    "term_uid": term["term"]["conceptId"],
                    "name": name,
                    "author_id": IMPORT_AUTHOR_ID,
                },
            )
            # raise ValueError("stop")
    return stats


def build_ct_package_term_uids(term, attr):
    uids = [
        package_name.replace(" ", "__") + "_" + term["term"]["conceptId"]
        for package_name in attr["catalogues"]
    ]
    del attr["catalogues"]
    attr["package_term_uids"] = uids


def compare_term_attributes(new, old):
    return (
        old["preferred_term"] == new["preferred_term"]
        and old["definition"] == new["definition"]
        and old["concept_id"] == new["concept_id"]
        and set(old["synonyms"]) == set(new["synonyms"])
    )


def compare_term_names(new, old):
    return (
        old["name"] == new["name"]
        and old["name_sentence_case"] == new["name_sentence_case"]
    )


def extract_term_names_and_attributes(term):
    names = []
    attributes = []
    for hv, tv, sponsor_name, packs in zip(
        term["hasversions"], term["values"], term["sponsor_names"], term["packages"]
    ):

        cdisc_name = tv["preferredTerm"]
        name_sentence_case = get_sentence_case_string(sponsor_name)
        name_value = {"name": sponsor_name, "name_sentence_case": name_sentence_case}
        name_version = {
            "value": name_value,
            "start_date": hv["start_date"],
            "end_date": hv.get("end_date"),
            "version": "1.0",
        }

        append_version(name_version, names, compare_term_names)

        catalogues = [pack["catalogue"] for pack in packs]
        synonyms = tv.get("synonyms", [])
        concept_id = term["term"]["conceptId"]
        definition = tv["definition"]
        attributes_value = {
            "synonyms": synonyms,
            "concept_id": concept_id,
            "definition": definition,
            "preferred_term": cdisc_name,
        }
        attributes_version = {
            "value": attributes_value,
            "start_date": hv["start_date"],
            "end_date": hv.get("end_date"),
            "version": "1.0",
            "catalogues": set(catalogues),
        }

        append_version(attributes_version, attributes, compare_term_attributes)

    return names, attributes


def merge_terms(staging_db_driver, sb_db_driver, sideload_data: bool = False):
    TERM_FETCH_BATCH = 100
    with staging_db_driver.session() as staging_session, sb_db_driver.session() as sb_session:
        total = count_versioned_terms(staging_session)
        LOGGER.info(f"Total staged terms: {total}")
        stats = None
        processed = 0
        for skip in range(0, total, TERM_FETCH_BATCH):
            LOGGER.info(
                f"Fetching terms {skip + 1}-{min(skip + TERM_FETCH_BATCH, total)}/{total}"
            )
            terms = fetch_versioned_terms(
                staging_session, skip=skip, limit=TERM_FETCH_BATCH
            )
            make_clean_term_package_names(terms)
            merge_term_roots(sb_session, terms, sideload_data)
            for term in terms:
                stats = merge_term_versions(
                    sb_session, term, stats=stats, sideload_data=sideload_data
                )
            processed += len(terms)
            LOGGER.info(f"Processed {processed}/{total} terms")
        print_stats(stats)


##### Link terms to codelists
def fetch_codelist_concept_ids(session):
    query = """MATCH (vcl:VersionedCodelist) RETURN vcl.conceptId as cid ORDER BY vcl.conceptId"""
    return [r["cid"] for r in run_single_query(session, query)]


def fetch_codelist_terms(session, concept_id):
    query = """
        MATCH (vcl:VersionedCodelist {conceptId: $cid})-[ht:HAS_TERM]->(vt:VersionedTerm)
        RETURN {term_cid: vt.conceptId, start_date: ht.start_date, end_date: ht.end_date, submval: ht.submissionValue} AS term
    """
    return [
        r["term"]
        for r in run_single_query(session, query, parameters={"cid": concept_id})
    ]


def fetch_codelist_ordinal_flags(session, sideload_data: bool = False):
    """Fetch a {codelist_uid: is_ordinal} map from the SB database, based on the latest codelist name value."""
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    query = f"""
        MATCH (clr:CTCodelistRoot{suffix})-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot{suffix})-[:LATEST]->(clnv:CTCodelistNameValue{suffix})
        RETURN clr.uid AS cid, coalesce(clnv.is_ordinal, false) AS is_ordinal
    """
    return {r["cid"]: r["is_ordinal"] for r in run_single_query(session, query)}


def link_terms_to_codelist(session, data, sideload_data: bool = False):
    suffix = SIDELOAD_SUFFIX if sideload_data else ""
    query = f"""
        MATCH (clr:CTCodelistRoot{suffix} {{uid: $cl_cid}})
        UNWIND $terms as term
            MATCH (tr:CTTermRoot{suffix} {{uid: term.term_cid}})<-[:HAS_TERM_ROOT]-(clterm:CTCodelistTerm{suffix} {{submission_value: term.submval}})
            MERGE (clr)-[ht:HAS_TERM {{start_date: datetime(term.start_date)}}]->(clterm)
            SET ht.end_date = datetime(term.end_date), ht.ordinal = term.ordinal
        """
    run_single_query(
        session, query, parameters={"cl_cid": data["cl_cid"], "terms": data["terms"]}
    )


def link_terms_to_codelists(
    staging_db_driver, sb_db_driver, sideload_data: bool = False
):
    with staging_db_driver.session() as staging_session, sb_db_driver.session() as sb_session:
        concept_ids = fetch_codelist_concept_ids(staging_session)
        ordinal_flags = fetch_codelist_ordinal_flags(
            sb_session, sideload_data=sideload_data
        )
        total = len(concept_ids)
        LOGGER.info(f"Total staged codelists with terms: {total}")
        for i, cid in enumerate(concept_ids):
            terms = fetch_codelist_terms(staging_session, cid)
            if terms:
                is_ordinal = ordinal_flags.get(cid, False)
                for term in terms:
                    term["ordinal"] = (
                        parse_ordinal_value(term["submval"]) if is_ordinal else None
                    )
                link_terms_to_codelist(
                    sb_session,
                    {"cl_cid": cid, "terms": terms},
                    sideload_data=sideload_data,
                )
            if (i + 1) % 100 == 0 or i + 1 == total:
                LOGGER.info(f"Linked terms for {i + 1}/{total} codelists")


def main():
    global IMPORT_AUTHOR_ID

    # Get sideload boolean argument
    parser = argparse.ArgumentParser(description="Process CDISC data.")
    parser.add_argument(
        "--sideload-data",
        action="store_true",
        help="Sideload the data in the MDR database to keep existing data",
    )
    args = parser.parse_args()
    sideload_data = args.sideload_data

    # Connect to both databases
    staging_db_driver = get_staging_db_driver()
    sb_db_driver = get_sb_db_driver()

    with sb_db_driver.session() as sb_session:
        create_indexes(sb_session, sideload_data=sideload_data)

    if check_sb_import_exists(sb_db_driver):
        LOGGER.info("Using system import user already present in OSB database")
        IMPORT_AUTHOR_ID = get_import_user_id(sb_db_driver)

    else:
        with sb_db_driver.session() as sb_session:
            sb_session.write_transaction(create_user, IMPORT_USERNAME)

    merge_libraries_catalogues_packages(
        staging_db_driver, sb_db_driver, sideload_data=sideload_data
    )

    merge_codelists(staging_db_driver, sb_db_driver, sideload_data=sideload_data)

    merge_terms(staging_db_driver, sb_db_driver, sideload_data=sideload_data)

    link_terms_to_codelists(
        staging_db_driver, sb_db_driver, sideload_data=sideload_data
    )


if __name__ == "__main__":
    main()
