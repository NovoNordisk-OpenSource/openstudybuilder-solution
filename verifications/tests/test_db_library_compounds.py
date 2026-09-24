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

from pytest_bdd import given, scenarios, then

from utils.utils import (
    REPORT_FILE_PATH,
    build_root_summary_return_statement,
    execute_query_and_append_result_to_file,
    get_db_connection,
    get_excluded_node_ids,
    get_gherkin_tags,
    get_logger,
    get_name_and_doc,
)

scenarios("library/compounds.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given("the library contains medicinal products")
def medicinal_products_exist():
    query = """
        MATCH (root:MedicinalProductRoot)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@given("the library contains pharmaceutical products")
def pharma_products_exist():
    query = """
        MATCH (root:PharmaceuticalProductRoot)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@given("the library contains pharmaceutical product ingredients")
def pharma_product_ingredients_exist():
    query = """
        MATCH (root:Ingredient)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@given("the library contains active substances")
def pharma_active_substances_exist():
    query = """
        MATCH (root:ActiveSubstanceRoot)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@given("the library contains compound aliases")
def compound_aliases_exist():
    query = """
        MATCH (root:CompoundAliasRoot)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then(
    "each PharmaceuticalProductValue node links to one PharmaceuticalProductRoot node"
)
def each_pharmaceutical_product_value_node_links_to_one_root_node(
    request, prepare_report_file
):
    """All PharmaceuticalProduct Value nodes link to a single Root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:PharmaceuticalProductValue)<-[hv:HAS_VERSION]-(root:PharmaceuticalProductRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of PharmaceuticalProduct Value nodes not linking to a single Root nodes: {cnt}"


@then("each ActiveSubstanceValue node links to one ActiveSubstanceRoot node")
def no_active_substance_value_node_links_to_several_root_nodes(
    request, prepare_report_file
):
    """All ActiveSubstance Value nodes link to a single Root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:ActiveSubstanceValue)<-[hv:HAS_VERSION]-(root:ActiveSubstanceRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of ActiveSubstance Value nodes not linking to a single Root nodes: {cnt}"


@then("each MedicinalProductValue node links to one MedicinalProductRoot node")
def each_medicinal_product_value_node_links_to_one_root_node(
    request, prepare_report_file
):
    """All MedicinalProduct Value nodes link to a single Root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:MedicinalProductValue)<-[hv:HAS_VERSION]-(root:MedicinalProductRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of MedicinalProduct Value nodes not linking to a single Root nodes: {cnt}"


@then("each MedicinalProductValue node links to one CompoundRoot node")
def each_compound_value_node_links_to_one_root_node(request, prepare_report_file):
    """Each MedicinalProductValue node links to a single CompoundRoot node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:MedicinalProductValue)-[:IS_COMPOUND]->(comp:CompoundRoot)
        WITH val, collect(DISTINCT comp) AS comps
        WHERE size(comps) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of MedicinalProduct Value nodes not linking to a single CompoundRoot node: {cnt}"


@then("each CompoundAliasValue node links to one CompoundRoot node")
def each_compound_alias_value_node_links_to_one_compound_root_node(
    request, prepare_report_file
):
    """Each CompoundAliasValue node links to one CompoundRoot node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:CompoundAliasValue)-[:IS_COMPOUND]->(root:CompoundRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of CompoundAliasValue nodes not linking to a single CompoundRoot node: {cnt}"


@then(
    "each MedicinalProductValue dose frequency CTTermContext node links to one CTTermRoot node"
)
def each_medicinal_product_value_dose_frequency_links_to_one_ct_term_root(
    request, prepare_report_file
):
    """Each MedicinalProductValue dose frequency CTTermContext node links to a single CTTermRoot node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    # A medicinal product may define zero or more dose frequencies, so the number of
    # HAS_DOSE_FREQUENCY relations is not constrained. Each one must still resolve to
    # exactly one CTTermRoot.
    query = f"""
        MATCH (val:MedicinalProductValue)-[:HAS_DOSE_FREQUENCY]->(ctt:CTTermContext)
        OPTIONAL MATCH (ctt)-[:HAS_SELECTED_TERM]->(term:CTTermRoot)
        WITH val, ctt, collect(DISTINCT term) AS terms
        WHERE size(terms) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of MedicinalProduct Value nodes with a dose frequency not linking to a single CTTermRoot node: {cnt}"


@then("each MedicinalProductValue node links to one CTTermContext dispenser node")
def each_medicinal_product_value_node_links_to_one_dispenser_node(
    request, prepare_report_file
):
    """Each MedicinalProductValue node links to a single CTTermContext dispenser node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:MedicinalProductValue)-[:HAS_DISPENSER]->(ctt:CTTermContext)
        WITH val, collect(DISTINCT ctt) AS terms
        WHERE size(terms) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of MedicinalProduct Value nodes not linking to a single CTTermContext dispenser node: {cnt}"


@then("each MedicinalProductValue node links to one CTTermContext delivery device node")
def no_medicinal_product_value_node_links_to_several_delivery_device_nodes(
    request,
    prepare_report_file,
):
    """Each MedicinalProductValue node links to a single CTTermContext delivery device node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:MedicinalProductValue)-[:HAS_DELIVERY_DEVICE]->(ctt:CTTermContext)
        WITH val, collect(DISTINCT ctt) AS terms
        WHERE size(terms) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of MedicinalProduct Value nodes not linking to a single CTTermContext delivery device node: {cnt}"


@then(
    "each PharmaceuticalProductValue node links to one CTTermContext route of administration node"
)
def no_pharmaceutical_product_value_node_links_to_several_roa_nodes(
    request,
    prepare_report_file,
):
    """Each PharmaceuticalProductValue node links to a single CTTermContext RoA node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:PharmaceuticalProductValue)-[:HAS_ROUTE_OF_ADMINISTRATION]->(ctt:CTTermContext)
        WITH val, collect(DISTINCT ctt) AS terms
        WHERE size(terms) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of PharmaceuticalProduct Value nodes not linking to a single CTTermContext RoA node: {cnt}"


@then(
    "each PharmaceuticalProductValue node links to one CTTermContext dosage form node"
)
def no_pharmaceutical_product_value_node_links_to_several_dosage_form_nodes(
    request,
    prepare_report_file,
):
    """Each PharmaceuticalProductValue node links to a single CTTermContext dosage form node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:PharmaceuticalProductValue)-[:HAS_DOSAGE_FORM]->(ctt:CTTermContext)
        WITH val, collect(DISTINCT ctt) AS terms
        WHERE size(terms) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of PharmaceuticalProduct Value nodes not linking to a single CTTermContext dosage form node: {cnt}"


@then(
    "each MedicinalProductValue node links to one or more PharmaceuticalProductRoot nodes"
)
def each_medicinal_product_value_node_links_to_one_or_more_pharma_product_nodes(
    request,
    prepare_report_file,
):
    """Each MedicinalProductValue node links to at least one PharmaceuticalProductRoot"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:MedicinalProductValue)-[:HAS_PHARMACEUTICAL_PRODUCT]->(pp:PharmaceuticalProductRoot)
        WITH val, collect(DISTINCT pp) AS pps
        WHERE size(pps) < 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of MedicinalProduct Value nodes not linking to any PharmaceuticalProductRoot nodes: {cnt}"


@then(
    "each MedicinalProductValue node links to one or more NumericValueWithUnitRoot dose value nodes"
)
def each_medicinal_product_value_node_links_to_one_or_more_dose_value_nodes(
    request,
    prepare_report_file,
):
    """Each MedicinalProductValue node links to at least one NumericValueWithUnitRoot dose value nodes"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:MedicinalProductValue)-[:HAS_DOSE_VALUE]->(dv:NumericValueWithUnitRoot)
        WITH val, collect(DISTINCT dv) AS dvs
        WHERE size(dvs) < 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of MedicinalProduct Value nodes not linking to any NumericValueWithUnitRoot dose value nodes: {cnt}"


@then(
    "each PharmaceuticalProductValue node links to one or more IngredientFormulation nodes"
)
def each_pharma_value_node_links_to_one_or_more_ingredient_formulation_node(
    request,
    prepare_report_file,
):
    """Each PharmaceuticalProductValue node links to one or more IngredientFormulation nodes"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:PharmaceuticalProductValue)-[:HAS_FORMULATION]->(if:IngredientFormulation)
        WITH val, collect(DISTINCT if) AS ifs
        WHERE size(ifs) < 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of PharmaceuticalProductValue nodes not linking to one or more IngredientFormulation nodes: {cnt}"


@then("each Ingredient node links to one ActiveSubstanceRoot node")
def each_ingredient_node_links_to_one_active_substance_root_node(
    request,
    prepare_report_file,
):
    """Each Ingredient node links to one ActiveSubstanceRoot node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:Ingredient)-[:HAS_SUBSTANCE]->(root:ActiveSubstanceRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of Ingredient nodes not linking to one ActiveSubstanceRoot node: {cnt}"


@then("each Ingredient node links to one LagTimeRoot node")
def each_pharma_ingredient_value_node_links_to_one_lag_time_root_node(
    request,
    prepare_report_file,
):
    """Each Ingredient node links to one LagTimeRoot node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:Ingredient)-[:HAS_LAG_TIME]->(root:LagTimeRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of Ingredient nodes not linking to one LagTimeRoot node: {cnt}"


@then("each Ingredient node links to one NumericValueWithUnitRoot strength node")
def each_pharma_ingredient_value_node_links_to_one_strength_node(
    request,
    prepare_report_file,
):
    """Each Ingredient node links to one NumericValueWithUnitRoot strength node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:Ingredient)-[:HAS_STRENGTH_VALUE]->(root:NumericValueWithUnitRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of Ingredient nodes not linking to one NumericValueWithUnitRoot strength node: {cnt}"


@then("each Ingredient node links to one NumericValueWithUnitRoot half life node")
def each_pharma_ingredient_value_node_links_to_one_half_life_node(
    request,
    prepare_report_file,
):
    """Each Ingredient node links to one NumericValueWithUnitRoot half life node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:Ingredient)-[:HAS_HALF_LIFE]->(root:NumericValueWithUnitRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) <> 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of Ingredient nodes not linking to one NumericValueWithUnitRoot half life node: {cnt}"


@then(
    "each ActiveSubstanceValue node links to zero or one DictionaryTermRoot UNII node"
)
def each_active_substance_value_node_links_to_zero_or_one_unii_node(
    request,
    prepare_report_file,
):
    """Each ActiveSubstanceValue node links to zero or one DictionaryTermRoot UNII node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (val:ActiveSubstanceValue)-[:HAS_UNII_VALUE]->(root:DictionaryTermRoot)
        WITH val, collect(DISTINCT root) AS roots
        WHERE size(roots) > 1
        {build_root_summary_return_statement('val')}
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
    ), f"Number of ActiveSubstanceValue node that link to multiple DictionaryTermRoot UNII nodes: {cnt}"
