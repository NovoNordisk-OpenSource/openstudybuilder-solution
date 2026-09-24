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


# regex that matches strings that contain only whitespace or punctuation, and no letters
NONSENSE_DEFINITION_REGEX = r"""^[\s!\"#$%&'()*+,\-.\/:;<=>?@\[\]^_`{|}~]+$"""
# dummy definitions found in production
DUMMY_DEFINITIONS = [
    "x",
    "x.",
    "TBD",
    "TBD.",
    "TBC",
    "null",
    "NA",
    "Definition not provided",
]


def test_study_selection_drop_relationships():
    """
    1. #For each StudySelection node, check that there are no missing relationships to next version StudySelection nodes
    """

    # For each StudySelection node, we need to find its connected StudyAction nodes to determine the temporal context.
    # We then check if there are any missing relationships between StudySelection nodes that should be present
    # based on the temporal context provided by the StudyAction nodes.
    # The relationships we are interested in are:
    # - STUDY_EPOCH_HAS_STUDY_VISIT
    # - STUDY_VISIT_HAS_SCHEDULE
    # - STUDY_EPOCH_HAS_DESIGN_CELL
    # - STUDY_ACTIVITY_HAS_INSTRUCTION
    # - STUDY_ELEMENT_HAS_DESIGN_CELL
    # - STUDY_ARM_HAS_BRANCH_ARM
    query = """
        MATCH (ss1:StudySelection)-[:AFTER]-(ss1_after_saction:StudyAction)
        OPTIONAL MATCH (ss1)<-[:BEFORE]-(ss1_before_saction:StudyAction)
        WITH ss1, ss1_after_saction,
        CASE 
            WHEN 
                ss1_before_saction IS NULL                              //it's the latest version (hasn't been before yet)
                AND NOT ss1_after_saction:Delete                        //it has not been deleted
            then 
                datetime({epochMillis: apoc.date.currentTimestamp()})   //enddate date as NOW as it has not been deleted
            WHEN 
                ss1_before_saction IS NULL                              //it's the latest version (hasn't been before yet)
                AND ss1_after_saction:Delete                            //it has been deleted
            then ss1_after_saction.date                                 // end date when deleted
            ELSE ss1_before_saction.date  //the final datetime of the version as it's a previos version
        END AS ss1_before_date                                          //final datetime
        //--------------------------------------------------------------------------------------------------------------
        /* 
            Match a connected study selection to ss1 that:
            - is a not final version 
            - and where the new version of that 
                study selection version is not connected to ss1 
            - AND END_DATE_SS1>END_DATE_SS2>START_DATE_SS1 !!!!THEY SHOULD BE CONNECTED AND THEY ARE NOT!!!
        */
        MATCH (ss1)-[ss1_ss2]-(ss2:StudySelection)<-[:BEFORE]-(ss2_saction:StudyAction)
                -[:AFTER]->(ss2_new_version:StudySelection) 
            WHERE 
                NOT EXISTS((ss2_new_version)--(ss1))                    // is not connected to ss1
                AND (   
                    ss2_saction.date<ss1_before_date                    //when end_date_ss2 < end_date_ss1
                    AND ss2_saction.date>ss1_after_saction.date         //when end_date_ss2 > start_date_ss1
                )
        //--------------------------------------------------------------------------------------------------------------
        WITH ss1, ss1_ss2, ss2, ss2_saction, ss2_new_version
        WHERE 
        TYPE(ss1_ss2) IN [
            "STUDY_EPOCH_HAS_STUDY_VISIT",
            "STUDY_VISIT_HAS_SCHEDULE",
            "STUDY_EPOCH_HAS_DESIGN_CELL",
            "STUDY_ACTIVITY_HAS_INSTRUCTION",
            "STUDY_ELEMENT_HAS_DESIGN_CELL",
            "STUDY_ARM_HAS_BRANCH_ARM"
        ]
        //------------------------------------------------CHECK SS3 NOT EXISTS (WASN'T A EDIT)--------------------------------
        OPTIONAL MATCH (ss2_new_version)-[ss2_ss3]-(ss3:StudySelection)
            WHERE TYPE(ss2_ss3)=TYPE(ss1_ss2)
                AND ss3.uid<>ss1.uid
        WITH ss1, ss1_ss2, ss2, ss2_saction, ss2_new_version
            WHERE ss3 IS NULL
        WITH 
            ss1, ss1_ss2, ss2, ss2_saction,
            collect([ss1, ss1_ss2, ss2, ss2_saction]) as n
        RETURN
            COUNT(n) as noncompliant_entity_cnt,
            COLLECT(distinct(labels(ss1)+labels(ss2))) as noncompliant_labels,
            COLLECT(distinct(ss1.uid+\",\"+ss2.uid)) as noncompliant_node_ids
    """

    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no non-compliant nodes, found {res[0][0]} "
        f"with labels {res[0][1]}"
    )


def test_remove_orphan_activity_instances():
    """
    1. No orphan ActivityInstanceRoot nodes should exist (nodes without LATEST relationship to ActivityInstanceValue)
    2. No orphan ActivityInstanceValue nodes should exist (nodes with no relationships)
    """

    # Check for orphan ActivityInstanceRoot nodes
    query = """
        MATCH (ai:ActivityInstanceRoot) 
        WHERE NOT EXISTS ((ai)-[:LATEST]->(:ActivityInstanceValue))
        RETURN 
            COUNT(ai) as orphan_root_count,
            COLLECT(DISTINCT ai.uid) as orphan_root_uids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no orphan ActivityInstanceRoot nodes, found {res[0][0]} "
        f"with uids: {res[0][1]}"
    )

    # Check for orphan ActivityInstanceValue nodes
    query = """
        MATCH (ai:ActivityInstanceValue) 
        WHERE NOT EXISTS ((ai)--())
        RETURN 
            COUNT(ai) as orphan_value_count,
            COLLECT(DISTINCT ai.uid) as orphan_value_uids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no orphan ActivityInstanceValue nodes, found {res[0][0]} "
        f"with uids: {res[0][1]}"
    )


def test_remove_orphan_activity_instance_classes():
    """
    No orphan ActivityInstanceClassValue nodes should exist (nodes without relationships)
    """

    # Check for orphan ActivityInstanceClassValue nodes
    query = """
    MATCH (aic:ActivityInstanceClassValue) WHERE NOT EXISTS ((aic)--())
    RETURN COUNT(aic) as orphan_class_count,
    COLLECT(DISTINCT aic.uid) as orphan_class_uids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no orphan ActivityInstanceClassValue nodes, found {res[0][0]} "
        f"with uids: {res[0][1]}"
    )


def test_remove_orphan_study_fields():
    """
    No orphan StudyField nodes should exist (nodes without relationships)
    """

    # Check for orphan StudyField nodes
    query = """
    MATCH (sf:StudyField) WHERE NOT EXISTS ((sf)--())
    RETURN COUNT(sf) as orphan_field_count,
    COLLECT(DISTINCT sf.uid) as orphan_field_uids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no orphan StudyField nodes, found {res[0][0]} "
        f"with uids: {res[0][1]}"
    )


def test_fix_instances_with_multiple_activities():
    """
    No ActivityInstanceValue nodes should be connected to multiple ActivityValue nodes through ActivityGrouping
    """

    # Check for ActivityInstanceValue nodes connected to multiple ActivityValue nodes through ActivityGrouping
    query = """
    MATCH (aiv:ActivityInstanceValue)<-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue)
        WITH aiv, collect(DISTINCT av) AS avs
        WITH aiv WHERE size(avs) > 1
    MATCH (root:ActivityInstanceRoot)-->(aiv)<-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue)
    RETURN count(DISTINCT root) as multiple_activities_count,
    COLLECT(DISTINCT root.uid) as multiple_activities_uids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no ActivityInstanceValue nodes connected to multiple ActivityValue nodes through ActivityGrouping, found {res[0][0]} "
        f"with uids: {res[0][1]}"
    )


def test_delete_unwanted_studies():
    LOGGER.info("Check for unwanted studies")

    unwanted = [
        "80_35_DELETE",
        "85_09_DELETE",
        "85_62_DELETE",
        "82_66_DELETE",
        "80_34_DELETE",
        "79_10_DELETE",
        "79_11_DELETE",
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


def test_remove_unwanted_sponsor_terms():
    LOGGER.info("Check for unwanted sponsor terms")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (tr:CTTermRoot)
        WHERE tr.uid IN ["CTTerm_001775", "CTTerm_001776", "CTTerm_001777"]
        RETURN tr
        """,
    )
    assert len(records) == 0, f"Found {len(records)} unwanted sponsor terms"


def test_remove_dummy_definitions():
    LOGGER.info("Check for dummy definitions in concept value nodes")

    query = f"""
        MATCH (root)-[:HAS_VERSION]->(value)
        WHERE value.definition is not null and (
            value.definition =~ "{NONSENSE_DEFINITION_REGEX}" OR
            value.definition IN {DUMMY_DEFINITIONS}
        )
        RETURN count(value) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER,
        query,
    )
    assert (
        res[0][0] == 0
    ), f"Expected no concept value nodes with dummy definitions, found {res[0][0]}"


def test_fix_baseline2_submission_values():
    query = """
        MATCH (clr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot)-[:LATEST]->(clnv:CTCodelistNameValue {name: "VisitType"})
        MATCH (clr)-[ht1:HAS_TERM]->(clt1:CTCodelistTerm {submission_value: "BASELINE 2"})-[htr1:HAS_TERM_ROOT]->(tr:CTTermRoot)
        MATCH (clr)-[ht2:HAS_TERM]->(clt2:CTCodelistTerm {submission_value: "BASELINE 2 VISIT TYPE"})-[htr2:HAS_TERM_ROOT]->(tr)
        WHERE ht1.end_date IS NULL AND ht2.end_date IS NULL
        RETURN count(clr) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER,
        query,
    )
    assert (
        res[0][0] == 0
    ), f"Expected no Baseline 2 visit type terms with two active submission values, found {res[0][0]}"


def test_set_author_id_for_cdisc_data():
    query = """
        MATCH ()-[ht:HAS_TERM|HAS_VERSION]->()
        WHERE ht.author_id IS NULL
        RETURN COUNT(ht) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER,
        query,
    )
    assert (
        res[0][0] == 0
    ), f"Expected no HAS_TERM or HAS_VERSION relationships missing author_id, found {res[0][0]}"

    query = """
        MATCH (p:CTPackage)
        WHERE p.author_id IS NULL
        RETURN COUNT(p) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER,
        query,
    )
    assert (
        res[0][0] == 0
    ), f"Expected no CTPackage nodes missing author_id, found {res[0][0]}"


def test_multiple_null_value_reasons():
    query = """
        MATCH (text_field:StudyTextField)-[:HAS_REASON_FOR_NULL_VALUE]->(context:CTTermContext)
        WITH text_field, collect(context) AS terms
        WITH * WHERE size(terms)>1
        RETURN count(text_field) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER,
        query,
    )
    assert (
        res[0][0] == 0
    ), f"Expected no StudyTextField nodes with multiple null value reasons, found {res[0][0]}"
