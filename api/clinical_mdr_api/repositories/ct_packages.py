from typing import Any

from neomodel import db

CODELIST_DATA_RETRIEVAL_SPECIFIC_QUERY = """
MATCH (old_package:CTPackage {name:$old_package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[old_versions:HAS_VERSION]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(old_codelist_root {uid:$codelist_uid})
WITH old_codelist_root, codelist_attr_val, max(old_versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([old_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS old_items

MATCH (new_package:CTPackage {name:$new_package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[new_versions:HAS_VERSION]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(new_codelist_root {uid:$codelist_uid})
WITH old_items, new_codelist_root, codelist_attr_val, max(new_versions.start_date) AS latest_date
WITH old_items, collect(apoc.map.fromValues([new_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS new_items
"""

TERM_DATA_RETRIEVAL_SPECIFIC_QUERY = """
MATCH (old_package:CTPackage {name:$old_package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_TERM]->
(package_term:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attr_val:CTTermAttributesValue)<-[old_versions:HAS_VERSION]-
(term_attr_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(old_term_root:CTTermRoot)<-[:HAS_TERM]-(old_codelist_root {uid:$codelist_uid})
WITH old_term_root,
    [(codelist_root)-[:HAS_TERM]->(old_term_root:CTTermRoot) | codelist_root.uid] AS codelists,
    term_attr_val,
    max(old_versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([old_term_root.uid, {
    value_node:term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS old_items

MATCH (new_package:CTPackage {name:$new_package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_TERM]->
(package_term:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attr_val:CTTermAttributesValue)<-[new_versions:HAS_VERSION]-
(term_attr_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(new_term_root:CTTermRoot)<-[:HAS_TERM]-(new_codelist_root {uid:$codelist_uid})
WITH old_items,
    new_term_root,
    [(codelist_root)-[:HAS_TERM]->(new_term_root) | codelist_root.uid] AS codelists,
    term_attr_val,
    max(new_versions.start_date) AS latest_date
WITH old_items, collect(apoc.map.fromValues([new_term_root.uid, {
    value_node: term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS new_items
"""

TERM_NOT_MODIFIED_CLAUSE_SPECIFIC_QUERY = """
,CASE WHEN old_items_map[common_item] = new_items_map[common_item] THEN
apoc.map.fromValues([
    'uid', common_item,
    'value_node', new_items_map[common_item].value_node,
    'change_date', new_items_map[common_item].change_date,
    'codelists', new_items_map[common_item].codelists
    ])
END AS not_modified
"""

TERM_RETURN_CLAUSE_SPECIFIC_QUERY = """
WITH collect(diff) as items_diffs, added_items, removed_items, collect(not_modified) as not_modified_items
RETURN added_items, removed_items, items_diffs, not_modified_items
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

PACKAGE_CODELISTS_DATA_RETRIEVAL = """
MATCH (package:CTPackage {name:$package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[versions:HAS_VERSION]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_root)
WITH codelist_root, codelist_attr_val, max(versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([codelist_root.uid, {
    uid: codelist_root.uid,
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS items
RETURN apoc.map.mergeList(items) AS items_map
"""

PACKAGE_TERMS_DATA_RETRIEVAL = """
MATCH (package:CTPackage {name:$package_name})-[:CONTAINS_CODELIST]->(package_codelist:CTPackageCodelist)-[:CONTAINS_TERM]->
(package_term:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attr_val:CTTermAttributesValue)<-[versions:HAS_VERSION]-
(term_attr_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(term_root:CTTermRoot)
WITH term_root,
    [(codelist_root)-[:HAS_TERM]->(term_root) | codelist_root.uid] AS codelists,
    term_attr_val,
    max(versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([term_root.uid, {
    uid: term_root.uid,
    value_node:term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS items
RETURN apoc.map.mergeList(items) AS items_map
"""

TERM_DIFF_CLAUSE = """
CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
apoc.map.fromValues([
    'uid', common_item,
    'value_node', apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
    'change_date', new_items_map[common_item].change_date,
    'codelists', new_items_map[common_item].codelists
    ])
END AS diff
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


@db.transaction
def get_ct_packages_codelist_changes(
    old_package_name: str, new_package_name: str, codelist_uid: str
) -> dict[str, Any]:
    query_params = {
        "old_package_name": old_package_name,
        "new_package_name": new_package_name,
        "codelist_uid": codelist_uid,
    }

    output = {}
    # codelists query
    complete_codelist_query = " ".join(
        [
            CODELIST_DATA_RETRIEVAL_SPECIFIC_QUERY,
            COMPARISON_PART,
            CODELIST_DIFF_CLAUSE,
            CODELIST_RETURN_CLAUSE,
        ]
    )
    codelist_ret, _ = db.cypher_query(complete_codelist_query, query_params)
    output["new_codelists"] = (
        sorted(codelist_ret[0][0], key=lambda ct_codelist: ct_codelist["change_date"])
        if len(codelist_ret) > 0
        else []
    )
    output["deleted_codelists"] = (
        sorted(codelist_ret[0][1], key=lambda ct_codelist: ct_codelist["change_date"])
        if len(codelist_ret) > 0
        else []
    )
    output["updated_codelists"] = codelist_ret[0][2] if len(codelist_ret) > 0 else []
    all_codelists_in_package = codelist_ret[0][3] if len(codelist_ret) > 0 else {}

    # terms query
    complete_term_query = " ".join(
        [
            TERM_DATA_RETRIEVAL_SPECIFIC_QUERY,
            COMPARISON_PART,
            TERM_DIFF_CLAUSE,
            TERM_NOT_MODIFIED_CLAUSE_SPECIFIC_QUERY,
            TERM_RETURN_CLAUSE_SPECIFIC_QUERY,
        ]
    )
    terms_ret, _ = db.cypher_query(complete_term_query, query_params)
    output["new_terms"] = (
        sorted(terms_ret[0][0], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["deleted_terms"] = (
        sorted(terms_ret[0][1], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["updated_terms"] = (
        sorted(terms_ret[0][2], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["not_modified_terms"] = (
        sorted(terms_ret[0][3], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )

    update_modified_codelists(
        output=output, all_codelists_in_package=all_codelists_in_package
    )
    return output


def are_optional_lists_different(left_list, right_list):
    if left_list == right_list:
        return False
    if left_list is None or right_list is None:
        return True
    return set(left_list) != set(right_list)


def are_terms_different(left_term, right_term):
    left_value = left_term["value_node"]
    right_value = right_term["value_node"]
    return (
        left_term["change_date"] != right_term["change_date"]
        or left_value["preferred_term"] != right_value["preferred_term"]
        or are_optional_lists_different(left_value["synonyms"], right_value["synonyms"])
        or left_value["definition"] != right_value["definition"]
    )


def are_codelists_different(left_cl, right_cl):
    left_value = left_cl["value_node"]
    right_value = right_cl["value_node"]
    return (
        left_cl["change_date"] != right_cl["change_date"]
        or left_value["preferred_term"] != right_value["preferred_term"]
        or are_optional_lists_different(left_value["synonyms"], right_value["synonyms"])
        or left_value["name"] != right_value["name"]
        or left_value["definition"] != right_value["definition"]
        or left_value["extensible"] != right_value["extensible"]
        or left_value["submission_value"] != right_value["submission_value"]
    )


def diff_dicts(left, right):
    # Compare two dicts returning the result
    # in the same format as apoc.diff.nodes()
    diff: dict[str, dict[Any, Any]] = {
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


def codelist_diff(left_cl, right_cl):
    left_value = left_cl["value_node"]
    right_value = right_cl["value_node"]

    value_diff = diff_dicts(left_value, right_value)
    result = {
        "uid": right_cl["uid"],
        "change_date": right_cl["change_date"],
        "value_node": value_diff,
    }
    return result


@db.transaction
def get_ct_packages_changes(
    old_package_name: str, new_package_name: str
) -> dict[str, Any]:
    output = {}
    # codelists query
    # Fetch the codelists and terms and do the comparison here.
    # Doing the comparison in cypher uses too much ram.
    query_params_old = {
        "package_name": old_package_name,
    }
    query_params_new = {
        "package_name": new_package_name,
    }
    old_codelists_ret, _ = db.cypher_query(
        PACKAGE_CODELISTS_DATA_RETRIEVAL, query_params_old
    )
    new_codelists_ret, _ = db.cypher_query(
        PACKAGE_CODELISTS_DATA_RETRIEVAL, query_params_new
    )

    new_codelists = new_codelists_ret[0][0]
    old_codelists = old_codelists_ret[0][0]
    old_uids = set(old_codelists.keys())
    new_uids = set(new_codelists.keys())
    added_uids = new_uids - old_uids
    deleted_uids = old_uids - new_uids
    added_codelists = [new_codelists[uid] for uid in added_uids]
    deleted_codelists = [old_codelists[uid] for uid in deleted_uids]

    # Find changed codelists
    cl_common_uids = new_uids & old_uids
    changed_codelists = []
    for uid in cl_common_uids:
        old_codelist = old_codelists[uid]
        new_codelist = new_codelists[uid]
        if are_codelists_different(old_codelist, new_codelist):
            changed_codelists.append(codelist_diff(old_codelist, new_codelist))

    output["new_codelists"] = (
        sorted(added_codelists, key=lambda ct_codelist: ct_codelist["change_date"])
        if len(added_codelists) > 0
        else []
    )
    output["deleted_codelists"] = (
        sorted(deleted_codelists, key=lambda ct_codelist: ct_codelist["change_date"])
        if len(deleted_codelists) > 0
        else []
    )
    output["updated_codelists"] = (
        sorted(changed_codelists, key=lambda ct_codelist: ct_codelist["change_date"])
        if len(changed_codelists) > 0
        else []
    )

    old_terms_ret, _ = db.cypher_query(PACKAGE_TERMS_DATA_RETRIEVAL, query_params_old)
    new_terms_ret, _ = db.cypher_query(PACKAGE_TERMS_DATA_RETRIEVAL, query_params_new)

    new_terms = new_terms_ret[0][0]
    old_terms = old_terms_ret[0][0]
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

    update_modified_codelists(output=output, all_codelists_in_package=new_codelists)
    return output


@db.transaction
def get_package_changes_by_year():
    query = """
    MATCH (p1)-[rel:NEXT_PACKAGE]->(p2)
    WITH p2.effective_date.year as year,
    rel.added_codelists as added_codelists, rel.updated_codelists as updated_codelists, rel.deleted_codelists as deleted_codelists,
    rel.added_terms as added_terms, rel.updated_terms as updated_terms, rel.deleted_terms as deleted_terms
    WITH year,
    sum(added_codelists) as added_codelists, sum(updated_codelists) as updated_codelists, sum(deleted_codelists) as deleted_codelists,
    sum(added_terms) as added_terms, sum(updated_terms) as updated_terms, sum(deleted_terms) as deleted_terms
    RETURN year, added_codelists, updated_codelists, deleted_codelists, added_terms, updated_terms, deleted_terms
    """
    yearly_aggregates = db.cypher_query(query)
    output = []
    if len(yearly_aggregates) > 0:
        for aggregate in yearly_aggregates[0]:
            output.append(
                {
                    "year": aggregate[0],
                    "added_codelists": aggregate[1],
                    "updated_codelists": aggregate[2],
                    "deleted_codelists": aggregate[3],
                    "added_terms": aggregate[4],
                    "updated_terms": aggregate[5],
                    "deleted_terms": aggregate[6],
                }
            )
    return output


def update_modified_codelists(
    output: dict[str, Any], all_codelists_in_package: dict[str, Any]
):
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
