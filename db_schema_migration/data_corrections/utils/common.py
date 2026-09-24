# Common queries and functions for data corrections
from data_corrections.utils.utils import run_cypher_query


def replace_term_by_deleting_query(
    bad_uid: str, good_uid: str
) -> tuple[str, dict[str, str]]:
    """
    Generate a Cypher query to remove an unwanted term,
    and move all relationships pointing to the unwanted term
    to the desired term.

    :param bad_uid: The UID of the term to be replaced.
    :param good_uid: The UID of the term to replace with.
    :return: A Cypher query string.
    """
    query = """
        MATCH (bad_term_root:CTTermRoot {uid: $bad_uid})
        MATCH (good_term_root:CTTermRoot {uid: $good_uid})
        CALL {
            WITH bad_term_root, good_term_root
            // Find all links to the bad term
            MATCH (entity)-[rel:HAS_SELECTED_TERM]->(bad_term_root)
            // Reconnect links to the good term
            MERGE (entity)-[:HAS_SELECTED_TERM]->(good_term_root)
        }
        // Remove the bad term and its relationships
        MATCH (tav:CTTermAttributesValue)-[:HAS_VERSION]-(tar:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(bad_term_root)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:HAS_VERSION]->(tnv:CTTermNameValue)
        MATCH (bad_clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(bad_term_root)
        DETACH DELETE bad_term_root, tar, tav, tnr, tnv, bad_clt
    """
    params = {"bad_uid": bad_uid, "good_uid": good_uid}
    return query, params


def replace_term_by_updating_dates_query(
    bad_uid: str, good_uid: str, codelist_uid: str
) -> tuple[str, dict[str, str]]:
    """
    Generate a Cypher query to solve a codelist term conflict
    by adding an end date to the bad term that matches the start date of the good term.

    :param bad_uid: The UID of the term to be replaced.
    :param good_uid: The UID of the term to replace with.
    :param codelist_uid: The UID of the codelist containing the terms.
    :return: A Cypher query string.
    """
    query = """
        MATCH (clr:CTCodelistRoot {uid: $codelist_uid})-[bad_ht:HAS_TERM]->(bad_clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(bad_term_root:CTTermRoot {uid: $bad_uid})
        MATCH (clr)-[good_ht:HAS_TERM]->(good_clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(good_term_root:CTTermRoot {uid: $good_uid})
        // Set the end date for the HAS_TERM of the bad term to the start date of the good term
        SET bad_ht.end_date = good_ht.start_date
    """
    params = {"bad_uid": bad_uid, "good_uid": good_uid, "codelist_uid": codelist_uid}
    return query, params


def delete_unwanted_study_query(study_number: str) -> tuple[str, dict[str, str]]:
    """
    Query for deleting an unwanted study and all its related nodes and relationships.
    """
    query = """
        MATCH (sr:StudyRoot)-[hsv]-(sv:StudyValue)
        WHERE (sr)--(:StudyValue {study_number: $study_number})
        CALL {
          WITH sr
          MATCH (sr)-[at:AUDIT_TRAIL]->(sa:StudyAction)
          MATCH (sa)-[before_after_sel:BEFORE|AFTER]->(ss:StudySelection)
          DETACH DELETE ss, sa
        } IN TRANSACTIONS
        CALL {
            WITH sv
            MATCH (sv)-[hsf]->(sf:StudyField)
            DETACH DELETE sf
        } IN TRANSACTIONS
        CALL {
            WITH sv
            MATCH (sv)-[hss]->(ss2:StudySelection)
            DETACH DELETE ss2
        } IN TRANSACTIONS
        DETACH DELETE sr, sv
    """
    params = {"study_number": study_number}
    return query, params


def find_codelist_uid(
    db_driver, *, name=None, concept_id=None, submission_value=None
) -> str | None:
    """
    Herlper to find the UID of a codelist given its name, submission value or concept id.
    """

    if name:
        where_clause = "(clr)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(:CTCodelistNameValue {name: $codelist_name})"
        params = {"codelist_name": name}
    elif concept_id:
        where_clause = "(clr)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(:CTCodelistAttributesValue {concept_id: $concept_id})"
        params = {"concept_id": concept_id}
    elif submission_value:
        where_clause = "(clr)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(:CTCodelistAttributesValue {submission_value: $submission_value})"
        params = {"submission_value": submission_value}
    else:
        raise ValueError(
            "At least one of name, concept_id or submission_value must be provided."
        )
    query = f"""
        MATCH (clr:CTCodelistRoot)
        WHERE {where_clause}
        RETURN clr.uid AS codelist_uid
    """
    results, _ = run_cypher_query(db_driver, query, params, quiet=True)
    if len(results) == 0:
        return None
    if len(results) > 1:
        raise RuntimeError(
            f"Multiple codelists identified by {params} found in the database."
        )
    return results[0][0]


# pylint: disable=too-many-arguments
def find_term_uid(
    db_driver,
    *,
    term_name=None,
    concept_id=None,
    codelist_uid=None,
    submission_value=None,
    library=None,
) -> str | None:
    """
    Helper to find the UID of a term given its name, concept id, submission value and/or codelist.
    """
    if submission_value and not codelist_uid:
        raise ValueError(
            "codelist_uid must be provided when searching by submission_value."
        )
    if not term_name and not concept_id and not submission_value:
        raise ValueError(
            "At least one of term_name, concept_id or submission_value must be provided."
        )
    params = {}
    where_clauses = []
    extra_matches = []
    if term_name:
        where_clauses.append(
            "(ctr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(:CTTermNameValue {name: $term_name})"
        )
        params["term_name"] = term_name
    if concept_id:
        where_clauses.append(
            "(ctr)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(:CTTermAttributesValue {concept_id: $concept_id})"
        )
        params["concept_id"] = concept_id
    if submission_value:
        extra_matches.append(
            "MATCH (ctr)<-[:HAS_TERM_ROOT]-(clt:CTCodelistTerm {submission_value: $submission_value})<-[ht:HAS_TERM]-(clr:CTCodelistRoot {uid: $codelist_uid})"
        )
        where_clauses.append("ht.end_date IS NULL")
        params["submission_value"] = submission_value
        params["codelist_uid"] = codelist_uid
    elif codelist_uid:
        extra_matches.append(
            "MATCH (clr:CTCodelistRoot {uid: $codelist_uid})-[ht:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ctr)"
        )
        where_clauses.append("ht.end_date IS NULL")
        params["codelist_uid"] = codelist_uid
    if library:
        where_clauses.append("(ctr)<-[:CONTAINS_TERM]-(:Library {name: $library})")
        params["library"] = library

    where_clause = " AND ".join(where_clauses)
    extra_match_clause = "\n".join(extra_matches)
    query = f"""
        MATCH (ctr:CTTermRoot)
        {extra_match_clause}
        WHERE {where_clause}
        RETURN ctr.uid AS term_uid
    """
    results, _ = run_cypher_query(db_driver, query, params, quiet=True)
    if len(results) == 0:
        return None
    if len(results) > 1:
        raise RuntimeError(
            f"Multiple terms identified by {params} found in the database."
        )
    return results[0][0]
