from typing import Any

from extensions.common import db_pagination_clause, db_sort_clause, query
from extensions.consumer_sample import models

FINAL_STATUS = "Final"

# "Final" is the CURRENT status of the name and of the attributes: the status of their
# latest HAS_VERSION. A term being revised (new Draft) or retired is left out until it is
# approved again. The codelist is only a lookup key: its own status is not checked.
CT_TERMS_QUERY = """
MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes:CTCodelistAttributesValue)
WHERE codelist_attributes.submission_value = $codelist_submission_value
MATCH (codelist_root)-[has_term:HAS_TERM]->(codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root:CTTermRoot)<-[:CONTAINS_TERM]-(library:Library)
WHERE has_term.end_date IS NULL
MATCH (term_root)-[:HAS_NAME_ROOT]->(name_root:CTTermNameRoot)-[:LATEST]->(name_value:CTTermNameValue)
MATCH (term_root)-[:HAS_ATTRIBUTES_ROOT]->(attributes_root:CTTermAttributesRoot)-[:LATEST]->(attributes_value:CTTermAttributesValue)
WITH DISTINCT codelist_root, has_term, codelist_term, term_root, name_root, name_value, attributes_root, attributes_value, library
CALL {
    WITH attributes_root, attributes_value
    MATCH (attributes_root)-[version_rel:HAS_VERSION]->(attributes_value)
    WITH version_rel
    ORDER BY toInteger(split(version_rel.version, '.')[0]) ASC, toInteger(split(version_rel.version, '.')[1]) ASC, version_rel.start_date ASC
    WITH collect(version_rel) AS version_rels
    RETURN last(version_rels) AS last_attributes_version_rel
}
CALL {
    WITH name_root, name_value
    MATCH (name_root)-[version_rel:HAS_VERSION]->(name_value)
    WITH version_rel
    ORDER BY toInteger(split(version_rel.version, '.')[0]) ASC, toInteger(split(version_rel.version, '.')[1]) ASC, version_rel.start_date ASC
    WITH collect(version_rel) AS version_rels
    RETURN last(version_rels) AS last_name_version_rel
}
WITH codelist_root, term_root, codelist_term, has_term, name_value, attributes_value, library, last_attributes_version_rel, last_name_version_rel
WHERE last_attributes_version_rel.status = $status AND last_name_version_rel.status = $status
WITH
    codelist_root.uid AS codelist_uid,
    term_root.uid AS term_uid,
    has_term.order AS order,
    has_term.ordinal AS ordinal,
    codelist_term.submission_value AS submission_value,
    attributes_value.concept_id AS concept_id,
    attributes_value.preferred_term AS nci_preferred_name,
    name_value.name AS sponsor_preferred_name,
    library.name AS library_name,
    last_attributes_version_rel.version AS attributes_version,
    last_attributes_version_rel.status AS attributes_status,
    last_name_version_rel.version AS name_version,
    last_name_version_rel.status AS name_status
"""


def get_ct_terms(
    codelist_submission_value: str,
    sort_by: models.SortByCTTerms,
    sort_order: models.SortOrder,
    page_size: int,
    page_number: int,
) -> tuple[list[dict[str, Any]], int]:
    """One page of the CT terms with Final name and attributes of a codelist, and the
    total number of such terms.

    The query runs twice, for the page and for the count; fine for a sample, a single
    query would be needed to avoid the second pass over the codelist."""
    sort_clause = db_sort_clause(
        sort_by.value, sort_order.value, secondary_sort_fields="term_uid"
    )
    pagination_clause, pagination_params = db_pagination_clause(page_size, page_number)
    params = {
        "codelist_submission_value": codelist_submission_value,
        "status": FINAL_STATUS,
    }

    rows = query(
        f"{CT_TERMS_QUERY} RETURN * {sort_clause} {pagination_clause}",
        params={**params, **pagination_params},
    )
    total_rows = query(f"{CT_TERMS_QUERY} RETURN count(*) AS total", params=params)
    total = total_rows[0]["total"] if total_rows else 0

    return rows, total
