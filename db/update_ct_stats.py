from neo4j import GraphDatabase
from os import environ
from neo4j.work.transaction import Transaction

# This reuses a lot of code from the API
# clinical_mdr_api/repositories/ct_packages.py

CODELIST_DATA_RETRIEVAL = """
MATCH (old_package:CTPackage {name:$old_package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[old_versions:HAS_VERSION]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(old_codelist_root)
WITH old_codelist_root, codelist_attr_val, max(old_versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([old_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS old_items

MATCH (new_package:CTPackage {name:$new_package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[new_versions:HAS_VERSION]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(new_codelist_root)
WITH old_items, new_codelist_root, codelist_attr_val, max(new_versions.start_date) AS latest_date
WITH old_items, collect(apoc.map.fromValues([new_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS new_items
"""

CODELIST_DIFF_CLAUSE = """
CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
apoc.map.fromValues([
    'uid', common_item,
    'value_node', apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
    'change_date', new_items_map[common_item].change_date,
    'is_change_of_codelist', true
    ])
END AS diff
"""

CODELIST_RETURN_CLAUSE = """
WITH collect(diff) as items_diffs, added_items, removed_items, new_items_map
RETURN added_items, removed_items, items_diffs, new_items_map
"""

PACKAGE_TERMS_DATA_RETRIEVAL = """
MATCH (package:CTPackage {name:$package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_TERM]->
(package_term:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attr_val:CTTermAttributesValue)<-[versions:HAS_VERSION]-
(term_attr_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(term_root:CTTermRoot)
WITH term_root,
    [(codelist_root)-[:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root) | codelist_root.uid] AS codelists,
    term_attr_val,
    max(versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([term_root.uid, {
    uid: term_root.uid,
    value_node:term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS items
RETURN apoc.map.mergeList(items) AS items_map
"""

COMPARISON_PART = """
// From pattern comprehensions we get list of maps, where each map represents data for specific codelist or term.
// The following section merge list of maps coming from pattern comprehensions into one map.
// The created maps store codelist uids or term uids as a keys and attributes values as a map values.
WITH old_items, new_items,
apoc.map.mergeList(old_items) AS old_items_map,
apoc.map.mergeList(new_items) AS new_items_map
// The following section creates arrays with codelist uids or terms uids
WITH old_items_map, new_items_map,
keys(old_items_map) AS old_items_uids,
keys(new_items_map) AS new_items_uids
// In the following section the comparison of uid arrays is made to identify if given codelist or term:
// was added, deleted, or is not moved in new package
WITH old_items_map, new_items_map, old_items_uids, new_items_uids,
apoc.coll.subtract(new_items_uids, old_items_uids) AS added_items,
apoc.coll.subtract(old_items_uids, new_items_uids) AS removed_items,
apoc.coll.intersection(old_items_uids, new_items_uids) AS common_items

// Collect uids of added items in the new package
WITH old_items_map, new_items_map, removed_items, common_items,
  [ added_item IN added_items | apoc.map.merge(apoc.map.fromValues(['uid',added_item]), new_items_map[added_item])] AS added_items

// Collect uids of removed items in the new package
WITH old_items_map, new_items_map, added_items, common_items,
  [ removed_item IN removed_items | apoc.map.merge(apoc.map.fromValues(['uid', removed_item]), old_items_map[removed_item])] AS removed_items

// The following section unwinds list with uids of items that are present in old package and new package
// to filter out common items from the map that contains all elements from new package.
UNWIND
  CASE WHEN common_items=[] THEN [NULL]
  ELSE common_items
  END AS common_item
// The following section makes the comparison of nodes that are present in both packages
WITH old_items_map, new_items_map, added_items, removed_items, common_items, common_item,
"""

STATS_UPDATE_QUERY = """
    MATCH (p1:CTPackage {name:$old_package_name})
    MATCH (p2:CTPackage {name:$new_package_name})
    MERGE (p1)-[rel:NEXT_PACKAGE]->(p2)
    SET 
      rel.added_terms=$added_terms,
      rel.deleted_terms=$deleted_terms,
      rel.updated_terms=$updated_terms,
      rel.last_refresh=datetime(),
      rel.added_codelists=$added_codelists,
      rel.deleted_codelists=$deleted_codelists,
      rel.updated_codelists=$updated_codelists
    """

DATABASE = environ.get("NEO4J_MDR_DATABASE")
NEO4J_PROTOCOL = environ.get("NEO4J_PROTOCOL", "neo4j")

uri = "{}://{}:{}".format(
    NEO4J_PROTOCOL,
    environ.get("NEO4J_MDR_HOST"), environ.get("NEO4J_MDR_BOLT_PORT")
)

driver = GraphDatabase.driver(
    uri,
    auth=(environ.get("NEO4J_MDR_AUTH_USER"), environ.get("NEO4J_MDR_AUTH_PASSWORD")),
)


def run_querystring(tx: Transaction, query: str) -> None:
    tx.run(query).consume()


def run_querystring_read(tx: Transaction, query: str):
    result = tx.run(query)
    return result.data()


def list_cats_and_packages(tx: Transaction):
    cypher = """
    MATCH (pack:CTPackage)--(cat:CTCatalogue)
    WHERE NOT (pack)-[:EXTENDS_PACKAGE]->(:CTPackage)
    WITH cat, pack
    ORDER BY pack.effective_date
    WITH cat, collect(pack) AS packages
    RETURN cat, packages
    """
    return run_querystring_read(tx, cypher)


def are_terms_different(left_term, right_term):
    left_value = left_term["value_node"]
    right_value = right_term["value_node"]
    return (
        left_term["change_date"] != right_term["change_date"]
        or left_value["preferred_term"] != right_value["preferred_term"]
        or left_value.get("synonyms") != right_value.get("synonyms")
        or left_value.get("definition") != right_value.get("definition")
    )


def diff_dicts(left, right):
    # Compare two dicts returning the result
    # in the same format as apoc.diff.nodes()
    diff = {
        "right_only": {},
        "left_only": {},
        "in_common": {},
        "different": {},
    }
    props = set(left.keys()) | set(right.keys())
    for prop in props:
        if prop in left and prop not in right:
            diff["left_only"][prop] = left[prop]
        elif prop in right and prop not in left:
            diff["right_only"][prop] = right[prop]
        elif left[prop] == right[prop]:
            diff["in_common"][prop] = right[prop]
        else:
            diff["different"][prop] = {
                "left": left[prop],
                "right": right[prop],
            }
    return diff


def term_diff(left_term, right_term):
    left_value = left_term["value_node"]
    right_value = right_term["value_node"]

    value_diff = diff_dicts(left_value, right_value)
    result = {
        "uid": right_term["uid"],
        "change_date": right_term["change_date"],
        "codelists": right_term["codelists"],
        "value_node": value_diff,
    }
    return result


def update_modified_codelists(output: dict, all_codelists_in_package: list):
    """
    The following function adds codelists that contains some terms from the
    * new_terms
    * deleted_terms
    * updated_terms
    sections to the 'updated_codelists' section to mark given codelist as updated.
    :param output:
    :param all_codelists_in_package:
    """
    updated_codelist_uids = [
        codelist["uid"] for codelist in output["updated_codelists"]
    ]
    for terms in [
        output["new_terms"],
        output["deleted_terms"],
        output["updated_terms"],
    ]:
        for term in terms:
            for codelist in term["codelists"]:
                # we only want to add a codelist to the 'updated_codelists' column if given codelist
                # is not already there and this codelist is from the package that we are currently comparing
                if (
                    codelist not in updated_codelist_uids
                    and codelist in all_codelists_in_package
                ):
                    # updated_codelists_uids is a helper list to track all uids
                    # of codelists in the package that is being compared
                    updated_codelist_uids.append(codelist)
                    output["updated_codelists"].append(
                        {
                            "uid": codelist,
                            "value_node": all_codelists_in_package[codelist][
                                "value_node"
                            ],
                            "change_date": term["change_date"],
                            "is_change_of_codelist": False,
                        }
                    )
    output["updated_codelists"].sort(key=lambda codelist: codelist["change_date"])


def process_packages(session, data):
    for row in data:
        cat_name = row["cat"]["name"]
        prev_package = row["packages"][0]
        for package in row["packages"][1:]:
            with session.begin_transaction() as tx:
                process_ct_packages_changes(tx, prev_package["name"], package["name"])
            prev_package = package


def process_ct_packages_changes(tx, old_package_name: str, new_package_name: str):
    print(f"\n{old_package_name} --> {new_package_name}")
    query_params = {
        "old_package_name": old_package_name,
        "new_package_name": new_package_name,
    }

    output = {}
    # codelists query
    complete_codelist_query = " ".join(
        [
            CODELIST_DATA_RETRIEVAL,
            COMPARISON_PART,
            CODELIST_DIFF_CLAUSE,
            CODELIST_RETURN_CLAUSE,
        ]
    )
    codelist_ret = tx.run(complete_codelist_query, query_params).data()

    output["new_codelists"] = codelist_ret[0]["added_items"]

    output["deleted_codelists"] = codelist_ret[0]["removed_items"]

    output["updated_codelists"] = codelist_ret[0]["items_diffs"]
    all_codelists_in_package = codelist_ret[0]["new_items_map"]

    # terms query
    # Fetch the terms and do the comparison here.
    # Doing the comparison in cypher uses too much ram.
    query_params_old = {
        "package_name": old_package_name,
    }
    query_params_new = {
        "package_name": new_package_name,
    }
    old_terms_ret = tx.run(PACKAGE_TERMS_DATA_RETRIEVAL, query_params_old).data()
    new_terms_ret = tx.run(PACKAGE_TERMS_DATA_RETRIEVAL, query_params_new).data()
    new_terms = new_terms_ret[0]['items_map']
    old_terms = old_terms_ret[0]['items_map']
    old_uids = set(old_terms.keys())
    new_uids = set(new_terms.keys())
    added_uids = new_uids - old_uids
    deleted_uids = old_uids - new_uids
    added_terms = [new_terms[uid] for uid in added_uids]
    deleted_terms = [old_terms[uid] for uid in deleted_uids]

    # Find changed terms
    common_uids = new_uids & old_uids
    changed_terms = []

    for uid in common_uids:
        old_term = old_terms[uid]
        new_term = new_terms[uid]
        if are_terms_different(old_term, new_term):
            changed_terms.append(term_diff(old_term, new_term))

    output["new_terms"] = (
        sorted(added_terms, key=lambda ct_term: ct_term["change_date"])
        if len(added_terms) > 0
        else []
    )
    output["deleted_terms"] = (
        sorted(deleted_terms, key=lambda ct_term: ct_term["change_date"])
        if len(deleted_terms) > 0
        else []
    )
    output["updated_terms"] = (
        sorted(changed_terms, key=lambda ct_term: ct_term["change_date"])
        if len(changed_terms) > 0
        else []
    )

    update_modified_codelists(
        output=output, all_codelists_in_package=all_codelists_in_package
    )

    params = {
        "old_package_name": old_package_name,
        "new_package_name": new_package_name,
        "added_terms": len(output["new_terms"]),
        "deleted_terms": len(output["deleted_terms"]),
        "updated_terms": len(output["updated_terms"]),
        "added_codelists": len(output["new_codelists"]),
        "deleted_codelists": len(output["deleted_codelists"]),
        "updated_codelists": len(output["updated_codelists"]),
    }
    row_format ="{:<10}" + "{:>10}"*3
    print(row_format.format("", "Added", "Updated", "Deleted"))
    print(row_format.format("Codelists", params["added_codelists"], params["updated_codelists"], params["deleted_codelists"]))
    print(row_format.format("Terms", params["added_terms"], params["updated_terms"], params["deleted_terms"]))

    tx.run(STATS_UPDATE_QUERY, params)


with driver.session(database=DATABASE) as session:
    with session.begin_transaction() as tx:
        packages = list_cats_and_packages(tx)
    process_packages(session, packages)
    session.close()

driver.close()
