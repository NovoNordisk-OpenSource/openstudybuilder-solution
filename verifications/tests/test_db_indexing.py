"""
This modules verifies that database nodes/relations look as expected.

Each test should execute a CYPHER query that returns one row with these columns:
 - check_id
 - check_description
 - noncompliant_entity_cnt
 - noncompliant_labels
 - noncompliant_node_ids

Result of each query is appended to `db_checks_results.csv` file.

"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
import os

from pytest_bdd import scenarios, then

from utils.utils import (
    REPORT_FILE_PATH,
    execute_query_and_append_result_to_file,
    get_db_connection,
    get_excluded_node_ids,
    get_gherkin_tags,
    get_logger,
    get_name_and_doc,
)

scenarios("general/indexing.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


def get_indexed_node_labels(prop=None):
    if prop:
        prop_statement = f"AND properties = ['{prop}']"
    else:
        prop_statement = ""
    query = f"""
        SHOW INDEXES
        YIELD entityType, labelsOrTypes, properties
        WHERE entityType = "NODE" AND size(labelsOrTypes) > 0 {prop_statement}
        RETURN labelsOrTypes
    """
    response, _ = db.cypher_query(query)
    return response


def get_constraints_for_node_labels(prop=None, const_type=None):
    if prop:
        prop_statement = f"AND properties = ['{prop}']"
    else:
        prop_statement = ""
    if const_type:
        type_statement = f"AND type = '{const_type}'"
    else:
        type_statement = ""
    query = f"""
        SHOW CONSTRAINTS
        YIELD entityType, labelsOrTypes, type, properties
        WHERE entityType = "NODE" {prop_statement} {type_statement}
        RETURN labelsOrTypes
    """
    response, _ = db.cypher_query(query)
    return response


@then("all nodes are included in at least one index")
def index_any_property(request, prepare_report_file):
    """Most nodes have at least one index on them"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "CTTermContext",
        "ActivityItem",
        "OdmAlias",
        "OdmFormalExpression",
        "OdmTranslatedText",
        "CTCodelistAttributesRoot",
        "CTCodelistNameRoot",
        "CTConfigValue",
        "CTTermAttributesRoot",
        "Conjunction",
        "Create",
        "Edit",
        "Delete",
        "StudyAction",
        "StudyArrayField",
        "StudyBooleanField",
        "StudyIntField",
        "StudyProjectField",
        "StudyTextField",
        "StudyTimeField",
        "StudyValue",
        "_Neodash_Dashboard",
        "Ingredient",
        "IngredientFormulation",
        "PharmaceuticalProductValue",
        "DatasetClassInstance",
        "DatasetInstance",
        "DatasetVariableInstance",
        "SponsorModelDatasetClassInstance",
        "SponsorModelDatasetInstance",
        "SponsorModelDatasetVariableInstance",
        "SponsorModelValue",
        "SponsorModelVariableClassInstance",
        "VariableClassInstance",
        "ScenarioVariableImplementation",
        "UpdateSoASnapshot",
        "SchemaMigration",
        "DataCorrection",
    ]

    labels_or_types = get_indexed_node_labels()

    query = f"""
        // All nodes should have an index
        MATCH (n) 
        WITH labels(n) AS labels
        UNWIND labels as label
        WITH distinct label as label
        UNWIND apoc.coll.flatten({labels_or_types}, true) as labelsOrTypes_unwind
        WITH label, COLLECT(distinct labelsOrTypes_unwind) as labels_or_types
        WHERE not label in labels_or_types
            and not label contains 'Counter'
            and not label =~ "(?i)[^\w]*Delete.*Root"
        WITH distinct label as label 
        where not label in {excluded_labels}
        with label
        ORDER BY label
        RETURN 
            COUNT(label) as noncompliant_entity_cnt,
            COLLECT(label) as noncompliant_labels, 
            'N/A' as noncompliant_node_ids   
    """

    result = execute_query_and_append_result_to_file(
        query,
        REPORT_FILE_PATH,
        check_id,
        check_description,
        tags=tags,
        excluded_node_ids=excluded_node_ids,
    )
    cnt = result["noncompliant_entity_cnt"]
    assert (
        cnt == 0
    ), f"Number of node labels that have no index on them: {cnt}, labels: {result.get('noncompliant_labels', [])}"


@then("node labels with 'uid' property have an index on 'uid' property")
def index_uid_property(request, prepare_report_file):
    """All node labels with 'uid' property have an index on 'uid' property"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    labels_or_types = get_indexed_node_labels(prop="uid")

    query = f"""
        // All node labels with uid property should have an index on uid

        // Get all labels of nodes having uid property
        MATCH (n) WHERE n.uid IS NOT null
        WITH labels(n) AS labels
        UNWIND labels as label
        WITH DISTINCT label as label
        ORDER BY label

        UNWIND apoc.coll.flatten({labels_or_types}, true) as labelWithUidIndex
        
        // Find labels without uid index   
        WITH label, collect (distinct labelWithUidIndex) as labelsWithUidIndex         
        WHERE not label in labelsWithUidIndex 
        and not label =~ "(?i)[^\w]*Delete.*Root"
        WITH distinct label as label 
        
        RETURN 
            COUNT(label) as noncompliant_entity_cnt,
            COLLECT(label) as noncompliant_labels,
            'N/A' as noncompliant_node_ids 
    """
    result = execute_query_and_append_result_to_file(
        query,
        REPORT_FILE_PATH,
        check_id,
        check_description,
        tags=tags,
        excluded_node_ids=excluded_node_ids,
    )
    cnt = result["noncompliant_entity_cnt"]
    assert (
        cnt == 0
    ), f"Number of node labels with 'uid' property that have no index on 'uid': {cnt}, labels: {result.get('noncompliant_labels', [])}"


@then("all root nodes have NODE_KEY constraint on 'uid' property")
def index_root_node_uid_unique(request, prepare_report_file):
    """DB: All Root node labels have NODE_KEY constraint  on 'uid' property
    apart from:
    CTCodelistAttributesRoot, CTCodelistNameRoot, CTTermAttributesRoot, SyntaxIndexingInstanceRoot, SyntaxIndexingTemplateRoot, SyntaxInstanceRoot, SyntaxTemplateRoot
    """

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "CTCodelistAttributesRoot",
        "CTCodelistNameRoot",
        "CTTermAttributesRoot",
        "CTTermNameRoot",
        "SyntaxIndexingInstanceRoot",
        "SyntaxIndexingTemplateRoot",
        "SyntaxInstanceRoot",
        "SyntaxPreInstanceRoot",
        "SyntaxTemplateRoot",
    ]

    labels_or_types = get_constraints_for_node_labels(prop="uid", const_type="NODE_KEY")

    query = f"""
        // All Root nodes should have an NODE_KEY constraint on uid

        // Get all Root nodes labels
        MATCH (n) 
        WHERE ALL(label IN labels(n) WHERE label =~ "(?i).*Root")
        WITH labels(n) AS labels
        UNWIND labels as label
        WITH distinct label as root_label
        WHERE not root_label in {excluded_labels}
        and not root_label =~ "(?i)[^\w]*Delete.*Root"
        with root_label
        ORDER BY root_label

        UNWIND apoc.coll.flatten({labels_or_types}, true) as labelWithUniqueUidIndex
        
        // Find root nodes labels without UNIQUE uid index
        WITH root_label, COLLECT(distinct labelWithUniqueUidIndex) as labelsWithUniqueUidIndex
        WHERE not root_label in labelsWithUniqueUidIndex
        WITH distinct root_label as root_label 

        RETURN 
            COUNT(root_label) as noncompliant_entity_cnt,
            COLLECT(root_label) as noncompliant_labels, 
            'N/A' as noncompliant_node_ids  
    """
    result = execute_query_and_append_result_to_file(
        query,
        REPORT_FILE_PATH,
        check_id,
        check_description,
        tags=tags,
        excluded_node_ids=excluded_node_ids,
    )
    cnt = result["noncompliant_entity_cnt"]
    assert (
        cnt == 0
    ), f"Number of Root node labels that do not have NODE_KEY constraint on 'uid' property: {cnt}, labels: {result.get('noncompliant_labels', [])}"
