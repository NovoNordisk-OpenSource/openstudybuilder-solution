from datetime import datetime
from enum import Enum
from typing import Any

from neomodel import db

from clinical_mdr_api.repositories.ct_packages import (
    CODELIST_DIFF_CLAUSE,
    CODELIST_RETURN_CLAUSE,
    COMPARISON_PART,
    TERM_DIFF_CLAUSE,
)


class CatalogueComparisonType(Enum):
    """Catalogue comparison type."""

    ATTRIBUTES_COMPARISON = "attributes"
    SPONSOR_COMPARISON = "sponsor"


@db.transaction
def get_ct_catalogues_changes(
    library_name: str | None,
    catalogue_name: str | None,
    comparison_type: CatalogueComparisonType,
    start_datetime: datetime,
    end_datetime: datetime,
) -> dict[str, Any]:
    filter_parameters = []
    if library_name is not None:
        filter_by_library_name = """
            EXISTS {{ MATCH (:Library {{name: $library_name}})-[:{LIBRARY_CT_REL}]->({CT_OBJECT}) }}"""
        filter_parameters.append(filter_by_library_name)
    if catalogue_name is not None:
        filter_by_catalogue_name = """
            EXISTS {{ MATCH (:CTCatalogue {{name: $catalogue_name}})-[:HAS_CODELIST]->(codelist_root) }}"""
        filter_parameters.append(filter_by_catalogue_name)
    filter_statements = (
        "AND " + " AND ".join(filter_parameters) if filter_parameters else ""
    )
    codelist_filter_statements = filter_statements.format(
        LIBRARY_CT_REL="CONTAINS_CODELIST", CT_OBJECT="codelist_root"
    )
    term_filter_statements = filter_statements.format(
        LIBRARY_CT_REL="CONTAINS_TERM", CT_OBJECT="term_root"
    )

    if comparison_type == CatalogueComparisonType.ATTRIBUTES_COMPARISON:
        relationship_type = "HAS_ATTRIBUTES_ROOT"
    else:
        relationship_type = "HAS_NAME_ROOT"

    # Single-pass: match versions < end_datetime once, split old/new via collected lists.
    codelist_data_retrieval = f"""
    MATCH (codelist_root:CTCodelistRoot)-[:{relationship_type}]->
        (ver_root)-[ver]->(ver_value)
    WHERE ver.start_date < datetime($end_datetime)
    {codelist_filter_statements}
    WITH codelist_root, ver_value, ver.start_date AS ver_date
    ORDER BY ver_date DESC
    WITH codelist_root,
        collect(ver_value) AS vals,
        collect(ver_date) AS dates
    WITH codelist_root, vals, dates,
        vals[0] AS new_val, dates[0] AS new_date,
        head([i IN range(0, size(dates)-1) WHERE dates[i] < datetime($start_datetime)]) AS old_idx
    WITH
        [x IN collect(CASE WHEN old_idx IS NOT NULL THEN
            apoc.map.fromValues([codelist_root.uid, {{value_node: vals[old_idx], change_date: dates[old_idx]}}])
        END) WHERE x IS NOT NULL] AS old_items,
        collect(
            apoc.map.fromValues([codelist_root.uid, {{value_node: new_val, change_date: new_date}}])
        ) AS new_items
    """

    # Single-pass term query: same strategy as codelist query.
    term_data_retrieval = f"""
    MATCH (codelist_root:CTCodelistRoot)-[:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)-[:{relationship_type}]->
        (ver_root)-[ver]->(ver_value)
    WHERE ver.start_date < datetime($end_datetime)
    {term_filter_statements}
    WITH term_root, ver_value, ver.start_date AS ver_date
    ORDER BY ver_date DESC
    WITH term_root,
        collect(ver_value) AS vals,
        collect(ver_date) AS dates
    WITH term_root, vals, dates,
        vals[0] AS new_val, dates[0] AS new_date,
        head([i IN range(0, size(dates)-1) WHERE dates[i] < datetime($start_datetime)]) AS old_idx
    WITH
        [x IN collect(CASE WHEN old_idx IS NOT NULL THEN
            apoc.map.fromValues([term_root.uid, {{value_node: vals[old_idx], codelists:[
                (term_root)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[:HAS_TERM]-(cl) | cl.uid], change_date: dates[old_idx]}}])
        END) WHERE x IS NOT NULL] AS old_items,
        collect(
            apoc.map.fromValues([term_root.uid, {{value_node: new_val, codelists:[
                (term_root)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[:HAS_TERM]-(cl) | cl.uid], change_date: new_date}}])
        ) AS new_items
    """

    term_return_clause = """
    WITH collect(diff) as items_diffs, added_items, removed_items
    RETURN added_items, removed_items, items_diffs
    """

    query_params = {
        "library_name": library_name,
        "catalogue_name": catalogue_name,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    }

    output = {}
    # codelist query
    complete_codelist_query = " ".join(
        [
            codelist_data_retrieval,
            COMPARISON_PART,
            CODELIST_DIFF_CLAUSE,
            CODELIST_RETURN_CLAUSE,
        ]
    )
    codelist_ret, _ = db.cypher_query(complete_codelist_query, query_params)
    output["new_codelists"] = (
        sorted(codelist_ret[0][0], key=lambda ct_codelist: ct_codelist["change_date"])
        if codelist_ret
        else []
    )
    output["deleted_codelists"] = (
        sorted(codelist_ret[0][1], key=lambda ct_codelist: ct_codelist["change_date"])
        if codelist_ret
        else []
    )
    output["updated_codelists"] = codelist_ret[0][2] if codelist_ret else []
    all_codelists_in_package = codelist_ret[0][3] if codelist_ret else {}

    # terms query
    complete_term_query = " ".join(
        [term_data_retrieval, COMPARISON_PART, TERM_DIFF_CLAUSE, term_return_clause]
    )
    terms_ret, _ = db.cypher_query(complete_term_query, query_params)
    output["new_terms"] = (
        sorted(terms_ret[0][0], key=lambda ct_term: ct_term["change_date"])
        if terms_ret
        else []
    )
    output["deleted_terms"] = (
        sorted(terms_ret[0][1], key=lambda ct_term: ct_term["change_date"])
        if terms_ret
        else []
    )
    output["updated_terms"] = (
        sorted(terms_ret[0][2], key=lambda ct_term: ct_term["change_date"])
        if terms_ret
        else []
    )

    # Add codelists containing changed terms to 'updated_codelists'.
    updated_codelist_uids: set[str] = {
        codelist["uid"] for codelist in output["updated_codelists"]
    }
    for terms in [
        output["new_terms"],
        output["deleted_terms"],
        output["updated_terms"],
    ]:
        for term in terms:
            for codelist in term["codelists"]:
                if (
                    codelist not in updated_codelist_uids
                    and codelist in all_codelists_in_package
                ):
                    updated_codelist_uids.add(codelist)
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

    return output
