"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import os

from data_corrections.utils.utils import get_db_driver, run_cypher_query
from migrations.utils.utils import get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()


def test_delete_unwanted_studies():
    LOGGER.info("Check for unwanted studies")

    unwanted = [
        ## XX1234 project
        "1335",
        "1336",
        "1337",
        "1372",
        "1373",
        "1374",
        "1375",
        "1379",
        "1385",
        "1430",
        "1431",
        "1447",
        "1448",
        "1476",
        "1477",
        "1530",
        "1558",
        "1569",
        "1582",
        "1595",
        "1604",
        "1630",
        "1632",
        "1659",
        "1687",
        "1689",
        "1690",
        "1768",
        "1833",
        "2175",
        "3511",
        "3785",
        "4093",
        # Dummy studies
        "0",
        "0001",
        "9000",
        "9001",
        "9002",
        "9004",
        "9999",
    ]
    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyValue)
        WHERE sv.study_number IN $unwanted
        RETURN sv
        """,
        params={"unwanted": unwanted},
    )
    assert len(records) == 0, f"Found {len(records)} unwanted studies"


def test_remove_na_version_properties():
    LOGGER.info("Check for unwanted versioning properties")
    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    records, _summary = run_cypher_query(
        DB_DRIVER,
        f"""
        // No LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationship have versioning properties
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
            AND size(keys(properties(lat))) > 0
        RETURN root, lat
        """,
    )
    assert len(records) == 0, f"Found {len(records)} unwanted versioning properties"


def test_add_missing_end_dates():
    LOGGER.info("Check for missing end dates")
    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    records, _summary = run_cypher_query(
        DB_DRIVER,
        f"""
        // Only last HAS_VERSION relationship should be without an end date for each root node
        MATCH (root)-[:HAS_VERSION]->()
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        CALL {{
                WITH root
                MATCH (root)-[hv:HAS_VERSION]-() 
                WITH hv
                // Sort by version and dates
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) DESC,
                    toInteger(split(hv.version, '.')[1]) DESC,
                    hv.end_date DESC,
                    hv.start_date DESC
                WITH collect(hv) as hvs
                // Return all except the very latest
                RETURN tail(hvs) as not_latest
            }}
        WITH root WHERE any(v IN not_latest WHERE v.end_date IS NULL)
        RETURN root
        """,
    )
    assert len(records) == 0, f"Found {len(records)} missing end dates"


def test_adjust_late_end_dates():
    LOGGER.info("Check for too late end dates")
    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    records, _summary = run_cypher_query(
        DB_DRIVER,
        f"""
        // Only last HAS_VERSION relationship should be without an end date for each root node
        MATCH (root)-[hv:HAS_VERSION]->(value)
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        WITH root, hv ORDER BY hv.start_date
        WITH root, collect(hv) as hv
        WHERE size(hv)>1
        // Check that start date of each version equals end date of the previous
        WITH root, [n IN range(1,size(hv)) WHERE hv[n-1].end_date > hv[n].start_date ] AS bad
        WITH root WHERE size(bad)>0
        RETURN root
        """,
    )
    assert len(records) == 0, f"Found {len(records)} too late end dates"


def test_adjust_cdisc_has_had_terms():
    LOGGER.info("Check for incorrect start and end dates on HAS/HAD_TERM relationships")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (clr)-[ht:HAS_TERM|HAD_TERM]-(t)
        WITH clr, ht, t, collect(DISTINCT t.concept_id) as cid ORDER BY cid, ht.start_date
        UNWIND cid as c
        WITH clr, c, collect(ht) as hts
        WHERE size(hts)>1
        // Check that start date of each version is equal or later than end date of the previous
        WITH clr, [n IN range(1,size(hts)) WHERE hts[n-1].end_date > hts[n].start_date ] AS bad
        WITH clr, bad WHERE size(bad)>0
        WITH DISTINCT clr AS root
        RETURN root
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} incorrect start and end dates on HAS/HAD_TERM relationships"


def test_remove_duplicated_terms_in_objective_cat():
    LOGGER.info("Check for unwanted sponsor terms in Objective Category codelist")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM|HAD_TERM]-(tr:CTTermRoot)<-[ct:CONTAINS_TERM]-(lib:Library {name: "CDISC"})
        MATCH (cnv:CTCodelistNameValue)<-[hcnv]-(nr:CTCodelistNameRoot)<-[hcnr:HAS_NAME_ROOT]-(clr)
        MATCH (ctnv:CTTermNameValue)<-[chnv]-(ctnr:CTTermNameRoot)<-[chtnr:HAS_NAME_ROOT]-(tr)
        WHERE cnv.name = 'Objective Category'
        CALL {
            WITH clr, ctnv
            WITH clr, collect(DISTINCT ctnv.name) as names
            MATCH (clr)-[ht:HAS_TERM|HAD_TERM]-(str:CTTermRoot)<-[cst:CONTAINS_TERM]-(lib:Library {name: "Sponsor"}) 
            MATCH (stnv:CTTermNameValue)<-[shnv]-(stnr:CTTermNameRoot)<-[shtnr:HAS_NAME_ROOT]-(str)
            WHERE trim(stnv.name) IN names
            RETURN str
        }
        RETURN DISTINCT str
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} duplicated terms in Objective Category codelist"


def test_capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter():
    LOGGER.info(
        "Check for lowercase first letter of SyntaxInstances/SyntaxPreInstances if non-Unit Template Parameter"
    )

    rs, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (tptr:TemplateParameterTermRoot)<-[:USES_VALUE]-(i_v:SyntaxInstanceValue)<--(:SyntaxInstanceRoot)
        WHERE NOT tptr.uid STARTS WITH "UnitDefinition_" AND i_v.name STARTS WITH "<p>["
        RETURN i_v.name, i_v.name_plain
        """,
    )
    assert all(
        i[0][4].isupper() for i in rs if i[0][4].strip()
    ), "Some SyntaxInstance names don't have a capital letter in the beginning."
    assert all(
        i[1][0].isupper() for i in rs if i[1][0].strip()
    ), "Some SyntaxInstance plain_names don't have a capital letter in the beginning."

    rs, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (tptr:TemplateParameterTermRoot)-->(:TemplateParameterTermValue)<-[:USES_VALUE]-(p_v:SyntaxPreInstanceValue)<--(:SyntaxPreInstanceRoot)
        WHERE NOT tptr.uid STARTS WITH "UnitDefinition_" AND p_v.name STARTS WITH "<p>["
        RETURN p_v.name, p_v.name_plain
        """,
    )
    assert all(
        i[0][4].isupper() for i in rs if i[0][4].strip()
    ), "Some SyntaxPreInstance names don't have a capital letter in the beginning."
    assert all(
        i[1][0].isupper() for i in rs if i[1][0].strip()
    ), "Some SyntaxPreInstance plain_names don't have a capital letter in the beginning."


def test_remove_duplicated_terms_in_operator():
    LOGGER.info("Check for unwanted terms in Operator codelist")

    nbr_records = 0
    for name in [">=", "<="]:
        records, _summary = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (:CTCodelistNameValue {name: "Operator"})<--(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(clr:CTCodelistRoot)-[badht:HAS_TERM]-(badtr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)--(:CTTermNameValue {name: $name})
            MATCH (badtr)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)--(:CTTermAttributesValue {code_submission_value: $name})
            RETURN DISTINCT badtr
            """,
            params={"name": name},
        )
        nbr_records += len(records)
    assert nbr_records == 0, f"Found {nbr_records} unwanted terms in Operator codelist"


def test_remove_duplicated_terms_in_finding_subcat():
    LOGGER.info("Check for unwanted terms in Finding Subcategory codelist")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (clnv:CTCodelistNameValue {name: 'Finding Subcategory Definition'})<-[:LATEST]-(clnr:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(clr)-[ht:HAS_TERM]-(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tav.code_submission_value IN ['COMPREHENSIO FIND_SUB_CAT', 'ORIENTATIO FIND_SUB_CAT']
        RETURN DISTINCT tr
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} duplicated terms in Finding Subcategory codelist"


def test_remove_duplicated_terms_in_frequency():
    LOGGER.info("Check for unwanted terms in Frequency codelist")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (clnv:CTCodelistNameValue {name: 'Frequency'})<-[:LATEST]-(clnr:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(clr)-[ht:HAS_TERM]-(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tav.code_submission_value = "OTH"
        RETURN DISTINCT tr
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} unwanted terms in Frequency codelist"
