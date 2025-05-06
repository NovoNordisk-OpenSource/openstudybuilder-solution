""" PRD Data Corrections, for release 1.7"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_007

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.7"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    delete_unwanted_studies(DB_DRIVER, LOGGER, run_label)
    remove_na_version_properties(DB_DRIVER, LOGGER, run_label)
    add_missing_end_dates(DB_DRIVER, LOGGER, run_label)
    adjust_late_end_dates(DB_DRIVER, LOGGER, run_label)
    adjust_cdisc_has_had_terms(DB_DRIVER, LOGGER, run_label)
    remove_duplicated_terms_in_objective_cat(DB_DRIVER, LOGGER, run_label)
    capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter(
        DB_DRIVER, LOGGER, run_label
    )
    remove_duplicated_terms_in_operator(DB_DRIVER, LOGGER, run_label)
    remove_duplicated_terms_in_finding_subcat(DB_DRIVER, LOGGER, run_label)
    remove_duplicated_terms_in_frequency(DB_DRIVER, LOGGER, run_label)


@capture_changes(task_level=1)
def delete_unwanted_study(db_driver, log, run_label, study_number):
    """
    ## Delete one complete study

    See `delete_unwanted_studies` for details.
    """
    desc = f"Deleting study number {study_number} from the database"
    log.info(f"Run: {run_label}, {desc}")

    # This query deletes a complete study from the database
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (sr:StudyRoot)-[hsv]-(sv:StudyValue)
        WHERE (sr)--(:StudyValue {study_number: $study_number}) 
        OPTIONAL MATCH (sr)-[at:AUDIT_TRAIL]->(sa:StudyAction)
        OPTIONAL MATCH (sa)-[before_after_sel:BEFORE|AFTER]->(ss:StudySelection)
        DETACH DELETE ss
        WITH *
        OPTIONAL MATCH (sv)-[hsf]->(sf:StudyField)
        DETACH DELETE sf
        WITH *
        OPTIONAL MATCH (sv)-[hss]->(ss2:StudySelection)
        DETACH DELETE ss2
        DETACH DELETE sr, sv, sa
        """,
        {"study_number": study_number},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    docs_only=True,
    verify_func=correction_verification_007.test_delete_unwanted_studies,
    has_subtasks=True,
)
def delete_unwanted_studies(db_driver, log, run_label):
    """
    ## Remove unwanted studies

    ### Change Description
    Some studies were imported into the production environment that should not be there.
    These are either test studies or related to the NN304 project.

    ### Nodes and relationships affected
    - All study nodes for the following study numbers are deleted:
      - Project NN304:
        - 1335, 1336, 1337, 1372, 1373, 1374, 1375
        - 1379, 1385, 1430, 1431, 1447, 1448, 1476
        - 1477, 1530, 1558, 1569, 1582, 1595, 1604
        - 1630, 1632, 1659, 1687, 1689, 1690, 1768
        - 1833, 2175, 3511, 3785, 4093
      - Test or demo:
        - 0, 0001, 9000, 9001, 9002, 9004, 9999
    - Expected changes: ~3500 nodes deleted, ~10000 relationships deleted
    """

    desc = "Deleting unwanted studies from the database"
    log.info(f"Run: {run_label}, {desc}")

    unwanted = [
        ## NN304 project
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
    any_did_update = False
    for study_number in unwanted:
        did_update = delete_unwanted_study(db_driver, log, run_label, study_number)
        any_did_update = any_did_update or did_update
    return any_did_update


@capture_changes(
    verify_func=correction_verification_007.test_remove_na_version_properties
)
def remove_na_version_properties(db_driver, log, run_label):
    """
    ## Remove versioning properties of NA template parameter value LATEST_FINAL

    ### Change Description
    The neo4j init script creates an "NA" template parameter
    with versioning properties on the `LATEST_FINAL` relationship.
    These should not exist as the versioning is carried by the `HAS_VERSION` relationship.

    - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/neo4j-mdr-db/pullrequest/112369)

    ### Nodes and relationships affected
    - `LATEST_FINAL` from `TemplateParameterValueRoot` node with uid "NA"
    - Expected changes: 6 relationship properties deleted
    """

    desc = "Deleting unwanted versioning properties for NA TemplateParameterValueRoot"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:TemplateParameterValueRoot {uid: "NA"})-[lf:LATEST_FINAL]-()
        SET lf = {}
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(verify_func=correction_verification_007.test_add_missing_end_dates)
def add_missing_end_dates(db_driver, log, run_label):
    """
    ## Add missing end date on HAS_VERSION relationships that are not the latest version.

    ### Change Description
    When a new version of an item is created the `HAS_VERSION`
    linking to the previous version must get an end date.
    There are a few old items where this has not worked.
    This correction fixes this by setting the missing end date
    to the start date of the following version.

    ### Nodes and relationships affected
    - Non-latest `HAS_VERSION` between `nnnRoot` and `nnnValue`, with missing `end_date` property.
    - Expected changes: 1 relationship property added
    """

    desc = "Adding end dates for HAS_VERSION relationships that are not the latest"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (root)-[:HAS_VERSION]->()
        WHERE none(label in labels(root) WHERE label IN [
            "ClassVariableRoot",
            "DatasetClassRoot",
            "DatasetRoot",
            "DatasetScenarioRoot",
            "DatasetVariableRoot",
            "StudyRoot"
        ])
        CALL {
            WITH root
            MATCH (root)-[hv:HAS_VERSION]-() 
            WITH hv
            // Sort by version and dates
            ORDER BY
                toInteger(split(hv.version, '.')[0]) DESC,
                toInteger(split(hv.version, '.')[1]) DESC,
                hv.end_date DESC,
                hv.start_date DESC
            WITH collect(hv) as has_versions
            UNWIND RANGE(1, size(has_versions)) as i
                WITH has_versions, has_versions[i] as v, has_versions[i-1] as vp
                WHERE v.end_date IS NULL
                SET v.end_date = vp.start_date
            }
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(verify_func=correction_verification_007.test_adjust_late_end_dates)
def adjust_late_end_dates(db_driver, log, run_label):
    """
    ## Adjust too late end date on HAS_VERSION relationships that are not the latest version.

    ### Change Description
    When a new version of an item is created the `HAS_VERSION`
    linking to the previous version must get an end date.
    There are a few old items where the end date is a
    fraction of a second later than the start date of the next version.
    This causes a slight overlap of versions which is not allowed.
    This correction fixes this by setting the missing end date
    to the start date of the following version.

    ### Nodes and relationships affected
    - Non-latest `HAS_VERSION` between `nnnRoot` and `nnnValue`,
      where property `end_date` is before the `start_date` of the next version.
    - Expected changes: ~9500 relationship properties changed
    """

    desc = (
        "Adjusting late end dates for HAS_VERSION relationships that are not the latest"
    )
    log.info(f"Run: {run_label}, {desc}")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (root)-[hv:HAS_VERSION]->(value)
        WHERE none(label in labels(root) WHERE label IN [
            "ClassVariableRoot",
            "DatasetClassRoot",
            "DatasetRoot",
            "DatasetScenarioRoot",
            "DatasetVariableRoot",
            "StudyRoot"
        ])
        WITH root, hv ORDER BY hv.start_date DESC
        WITH root, collect(hv) as hv
        WHERE size(hv)>1
        UNWIND RANGE(1, size(hv)) as n
            WITH n, hv[n] as vprev, hv[n-1] as v
            WHERE vprev.end_date > v.start_date
            SET vprev.end_date = v.start_date
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_007.test_adjust_cdisc_has_had_terms
)
def adjust_cdisc_has_had_terms(db_driver, log, run_label):
    """
    ## Correct start and end dates of HAD_TERM relationships.

    ### Change Description
    When a codelist term is removed from a codelist,
    it is linked to the codelist root via a `HAD_TERM` relationship.
    A new term with the same concept it may then be added,
    linked via a `HAS_TERM` relationship.
    There are a few old items where the end date of the `HAD_TERM`
    does not match the start date of the `HAS_TERM` that replaces it.
    This correction fixes this by changing the start
    and end dates of the terms to put them in sequence.

    ### Nodes and relationships affected
    - `HAD_TERM` and `HAS_TERM` between
      - `CTCodelistRoot` with uids "C66726" and terms with concept id "C134876"
      - `CTCodelistRoot` with uids "C74456" and terms with concept id "C102286"
    - Expected changes: 3 relationship properties changed
    """

    desc = "Adjusting dates for term C134876 in codelist C66726, and term C102286 in codelist C74456"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot {uid: "C66726"})
        MATCH (clr)-[hdt:HAD_TERM {start_date: datetime("2018-12-21T00:00:00Z")}]-(t1 {concept_id: "C134876"}) 
        MATCH (clr)-[hst:HAS_TERM {start_date: datetime("2018-12-21T00:00:00Z")}]-(t2 {concept_id: "C134876"})
        SET hst.start_date = hdt.end_date
        """,
    )

    counters1 = summary.counters
    print_counters_table(counters1)

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot {uid: "C74456"})
        MATCH (clr)-[hdt1:HAD_TERM {start_date: datetime("2014-09-26T00:00:00Z")}]-(t1 {concept_id: "C102286"}) 
        MATCH (clr)-[hdt2:HAD_TERM {start_date: datetime("2018-12-21T00:00:00Z")}]-(t2 {concept_id: "C102286"})
        MATCH (clr)-[hst:HAS_TERM {start_date: datetime("2020-11-06T00:00:00Z")}]-(t3 {concept_id: "C102286"})
        SET hdt1.end_date = hdt2.start_date
        SET hst.start_date = hdt2.end_date
        """,
    )

    counters2 = summary.counters
    print_counters_table(counters2)
    return counters1.contains_updates or counters2.contains_updates


@capture_changes(
    verify_func=correction_verification_007.test_remove_duplicated_terms_in_objective_cat
)
def remove_duplicated_terms_in_objective_cat(db_driver, log, run_label):
    """
    ## Remove unwanted sponsor terms from Objective Category codelist.

    ### Change Description
    At some point, a bug in the import script created and added sponsor defined terms
    to the "Objective Category" codelist.
    These terms have the same names as the CDISC terms that are supposed to be in the list.
    The result is that every term appears twice, as one CDISC and one sponsor defined version.
    This correction removes the sponsor defined terms.
    Any node linking to one of these sponsor defined terms is modified to instead link to the
    corresponding CDISC term.

    ### Nodes and relationships affected
    - All nodes and relationships related to the unwanted terms are deleted:
      - Term root: `CTTermRoot`,
      - Term names: `CTTermNameRoot`, `CTTermNameValue`, `HAS_NAME_ROOT`, `HAS_VERSION`
      - Term attributes: `CTTermAttributesRoot`, `CTTermAttributesValue`, `HAS_ATTRIBUTES_ROOT`, `HAS_VERSION`
    - Items linking to the affected terms are modified:
      - `HAS_CATEGORY` relationships are moved to point at the `CTTermRoot` of the corresponding CDISC term.
    - Expected changes: 25 nodes deleted, 60 relationships deleted, 10 relationships created
    """

    desc = "Remove unwanted sponsor terms in Objective Category codelist"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM|HAD_TERM]-(tr:CTTermRoot)<-[ct:CONTAINS_TERM]-(lib:Library {name: "CDISC"})
        MATCH (cnv:CTCodelistNameValue)<-[hcnv]-(nr:CTCodelistNameRoot)<-[hcnr:HAS_NAME_ROOT]-(clr)
        MATCH (ctnv:CTTermNameValue)<-[chnv]-(ctnr:CTTermNameRoot)<-[chtnr:HAS_NAME_ROOT]-(tr)
        WHERE cnv.name = 'Objective Category'
        WITH clr, collect(DISTINCT ctnv.name) as names
        UNWIND names as name
            MATCH (clr)-[ht:HAS_TERM|HAD_TERM]-(str:CTTermRoot)<-[cst:CONTAINS_TERM]-(lib:Library {name: "Sponsor"}) 
            MATCH (stnv:CTTermNameValue)<-[shnv]-(stnr:CTTermNameRoot)<-[shtnr:HAS_NAME_ROOT]-(str)
            WHERE trim(stnv.name) = name
            MATCH (stav:CTTermAttributesValue)<-[shav]-(star:CTTermAttributesRoot)<-[shtar:HAS_ATTRIBUTES_ROOT]-(str)
            OPTIONAL MATCH (str)<-[hascat:HAS_CATEGORY]-(termuser)
            WITH *, collect(termuser) as users
            MATCH (clr)-[:HAS_TERM]-(cdisc_term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(CTTermNameRootValue {name: name})
            FOREACH (n IN users | MERGE (n)-[:HAS_CATEGORY]->(cdisc_term_root))
            DETACH DELETE str, star, stav, stnr, stnv
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_007.test_capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter
)
def capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter(
    db_driver, log, run_label
):
    """
    ## Capitalize first letter of name/name_plain if the word is a non-Unit Template Parameter.

    ### When the first word of the `name` property of any `SyntaxInstanceValue`/`SyntaxPreInstanceValue` is a Template Parameter other than a Unit,
    then its first letter should be in uppercase, in which case its `name_plain` property's first letter also should be in uppercase.

    ### Nodes Affected
    - `SyntaxInstanceValue`
    - `SyntaxPreInstanceValue`
    """
    log.info(
        f"Run: {run_label}, Capitalizing first letter of name/name_plain of SyntaxInstances/SyntaxPreInstances if it is a non-Unit Template Parameter."
    )

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (tptr:TemplateParameterTermRoot)<-[:USES_VALUE {index: 1, position: 1}]-(i_v:SyntaxInstanceValue)<--(:SyntaxInstanceRoot)
        WHERE NOT tptr.uid STARTS WITH "UnitDefinition_" AND i_v.name STARTS WITH "<p>[" AND substring(i_v.name, 4, 1) =~ "[a-z]"
        SET i_v.name = "<p>[" + toUpper(substring(i_v.name, 4, 1)) + substring(i_v.name, 5)
        SET i_v.name_plain = toUpper(substring(i_v.name_plain, 0, 1)) + substring(i_v.name_plain, 1)
        """,
    )
    counters1 = summary.counters
    print_counters_table(counters1)

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (tptr:TemplateParameterTermRoot)-->(:TemplateParameterTermValue)<-[:USES_VALUE {index: 1, position: 1}]-(p_v:SyntaxPreInstanceValue)<--(:SyntaxPreInstanceRoot)
        WHERE NOT tptr.uid STARTS WITH "UnitDefinition_" AND p_v.name STARTS WITH "<p>[" AND substring(p_v.name, 4, 1) =~ "[a-z]"
        SET p_v.name = "<p>[" + toUpper(substring(p_v.name, 4, 1)) + substring(p_v.name, 5)
        SET p_v.name_plain = toUpper(substring(p_v.name_plain, 0, 1)) + substring(p_v.name_plain, 1)
        """,
    )

    counters2 = summary.counters
    print_counters_table(counters2)

    return counters1.contains_updates or counters2.contains_updates


@capture_changes(
    verify_func=correction_verification_007.test_remove_duplicated_terms_in_operator
)
def remove_duplicated_terms_in_operator(db_driver, log, run_label):
    """
    ## Remove unwanted sponsor terms from Operator codelist.

    ### Change Description
    The two operator terms >= and <= has changed submission value to ≥ and ≤,
    but a bug in the import script did not retire the old terms.
    The two old terms are now present in the Operator codelist as well as the new terms.
    This correction removes the old terms by setting and end date equal to the start date of the new terms.

    ### Nodes and relationships affected
    - The `HAS_TERM` relationships linking the unwanted `CTTermRoot` nodes to the Operator codelist `CTCodelistRoot` node
      are deleted and replaced with `HAD_TERM` relationships.
    - The end_date property of the new `HAD_TERM` relationships is set to the start_date of the corresponding `HAS_TERM` relationships.
    - Expected changes: 2 relationships deleted, 2 relationships created
    """

    desc = "Remove unwanted terms in Operator codelist"
    log.info(f"Run: {run_label}, {desc}")

    contains_updates = False

    for badname, goodname in ((">=", "≥"), ("<=", "≤")):
        _, summary = run_cypher_query(
            db_driver,
            """
                MATCH (:CTCodelistNameValue {name: "Operator"})<--(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(clr:CTCodelistRoot)-[badht:HAS_TERM]-(badtr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)--(:CTTermNameValue {name: $badname})
                MATCH (badtr)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)--(:CTTermAttributesValue {code_submission_value: $badname})
                MATCH (clr)-[goodht:HAS_TERM]-(goodtr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)--(:CTTermNameValue {name: $badname})
                MATCH (goodtr)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)--(:CTTermAttributesValue {code_submission_value: $goodname})
                WITH DISTINCT clr, badht, badtr, goodht, goodtr
                MERGE (clr)-[hadterm:HAD_TERM {start_date: badht.start_date, end_date: goodht.start_date}]->(badtr)
                WITH badht
                DELETE badht
            """,
            params={"badname": badname, "goodname": goodname},
        )

        counters = summary.counters
        print_counters_table(counters)
        contains_updates = contains_updates or counters.contains_updates
    return contains_updates


@capture_changes(
    verify_func=correction_verification_007.test_remove_duplicated_terms_in_finding_subcat
)
def remove_duplicated_terms_in_finding_subcat(db_driver, log, run_label):
    """
    ## Remove unwanted sponsor terms from Finding Subcategory Definition codelist.

    ### Change Description
    Because of typos in the data used when importing the Finding Subcategory codelist,
    two terms were created twice.
    The duplicates have a typo in the submission value.
    This causes the terms "Orientation" and "Comprehension" appear twice in the codelist.
    Since the unwanted terms have incorrect submission values, there is nothing else linking to them.
    The unwanted terms should be removed.

    ### Nodes and relationships affected
    - All nodes and relationships related to the unwanted terms are deleted:
      - Term root: `CTTermRoot`,
      - Term names: `CTTermNameRoot`, `CTTermNameValue`, `HAS_NAME_ROOT`, `HAS_VERSION`
      - Term attributes: `CTTermAttributesRoot`, `CTTermAttributesValue`, `HAS_ATTRIBUTES_ROOT`, `HAS_VERSION`
    - Expected changes: 10 nodes deleted, 28 relationships deleted
    """

    desc = "Remove unwanted sponsor terms in Finding Subcategory codelist"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clnv:CTCodelistNameValue {name: 'Finding Subcategory Definition'})<-[:LATEST]-(clnr:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(clr)-[ht:HAS_TERM]-(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tav.code_submission_value IN ['COMPREHENSIO FIND_SUB_CAT', 'ORIENTATIO FIND_SUB_CAT']
        MATCH (tnv:CTTermNameValue)<-[:HAS_VERSION]-(tnr:CTTermNameRoot)<-[:HAS_NAME_ROOT]-(tr)
        DETACH DELETE tr, tar, tav, tnr, tnv
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_007.test_remove_duplicated_terms_in_frequency
)
def remove_duplicated_terms_in_frequency(db_driver, log, run_label):
    """
    ## Remove unwanted sponsor terms from Frequency codelist.

    ### Change Description
    At some point an unwanted term with name "Other" and submission value "OTH" was added to the Frequency codelist.
    This unwanted term has the same name as the CDISC term that is supposed to be in the list.
    Remove this unwanted term only from this codelist.

    ### Nodes and relationships affected
    - The `HAS_TERM` relationship between the Frequency codelist `CTCodelistRoot` node
      and the unwanted `CTTermRoot` node is deleted.
    - Expected changes: 1 relatiohship deleted
    """

    desc = "Remove unwanted sponsor terms in Frequency codelist"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clnv:CTCodelistNameValue {name: 'Frequency'})<-[:LATEST]-(clnr:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(clr)-[ht:HAS_TERM]-(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tav.code_submission_value = "OTH"
        DELETE ht
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


if __name__ == "__main__":
    main()


