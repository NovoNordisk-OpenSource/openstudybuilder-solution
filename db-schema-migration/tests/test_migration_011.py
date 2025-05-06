import json
import os

import pytest

from migrations import migration_011
from migrations.utils.utils import (
    api_get_paged,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_011 import TEST_DATA
from tests.utils.utils import clear_db

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=broad-except

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

db = get_db_connection()
DB_DRIVER = get_db_driver()
logger = get_logger(os.path.basename(__file__))


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_011.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_change_value_of_name_property_of_activity_instance_class():
    logger.info("Check wrong names for Activity Instance Class")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "Observation"})<--(r1:ActivityInstanceClassRoot)
        RETURN COUNT(*) as count;
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with name: Observation"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Finding"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "NumericFinding"})
        RETURN COUNT(*) as count;
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with name: NumericFinding"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Finding"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "CategoricFinding"})
        RETURN COUNT(*) as count;
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with name: CategoricFinding"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Finding"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "TextualFinding"})
        RETURN COUNT(*) as count;
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with name: TextualFinding"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Event"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "Event"})
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with name: Event"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Intervention"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "Intervention"})
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with name: Intervention"""


@pytest.mark.order(
    after="test_change_value_of_name_property_of_activity_instance_class"
)
def test_repeat_change_value_of_name_property_of_activity_instance_class(migration):
    assert not migration_011.change_value_of_name_property_of_activity_instance_class(
        DB_DRIVER, logger
    )


def test_add_level_property_to_activity_instance_class():
    logger.info("Check wrong levels for Activity Instance Class")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)
        WHERE v1.name IN [
            'GeneralObservation',
            'SubjectObservation',
            'Observation',
            'SpecialPurpose',
            'DeviceSpecialPurpose',
            'Finding',
            'Event',
            'Intervention',
            'Demographics',
            'Comments',
            'SubjectVisits',
            'DeviceIdentifiers',
            'NumericFindings',
            'CategoricFindings',
            'TextualFindings',
            'Events',
            'Interventions'
        ] AND v1.level IS NULL
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with level: NULL"""


@pytest.mark.order(after="test_add_level_property_to_activity_instance_class")
def test_repeat_add_level_property_to_activity_instance_class(migration):
    assert not migration_011.add_level_property_to_activity_instance_class(
        DB_DRIVER, logger
    )


def test_update_parent_class_relationship_of_activity_instance_class():
    logger.info("Check all expected Activity Instance Classes are present")
    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)
        WHERE v1.name IN [
            'GeneralObservation',
            'SubjectObservation',
            // 'Observation', WILL BE ADDED WITH A REQUEST TO THE API ON PRD
            'SpecialPurpose',
            'DeviceSpecialPurpose',
            'Finding',
            'Event',
            'Intervention',
            'Demographics',
            'Comments',
            'SubjectVisits',
            'DeviceIdentifiers',
            'NumericFindings',
            'CategoricFindings',
            'TextualFindings',
            'Events',
            'Interventions'
        ]
        RETURN COLLECT(DISTINCT v1.name) as names
        """,
    )
    missing_activity_instance_classes = {
        "GeneralObservation",
        "SubjectObservation",
        "SpecialPurpose",
        "DeviceSpecialPurpose",
        "Finding",
        "Event",
        "Intervention",
        "Demographics",
        "Comments",
        "SubjectVisits",
        "DeviceIdentifiers",
        "NumericFindings",
        "CategoricFindings",
        "TextualFindings",
        "Events",
        "Interventions",
    } - set(records[0]["names"])

    assert (
        not missing_activity_instance_classes
    ), "Some Activity Instance Classes are missing"

    logger.info("Check wrong parent_class relationships for Activity Instance Class")
    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["Demographics", "Comments", "SubjectVisits"]
        MATCH (v2:ActivityInstanceClassValue {name: "SpecialPurpose"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(r2))
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with no parent_class relationship"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["DeviceIdentifiers"]
        MATCH (v2:ActivityInstanceClassValue {name: "DeviceSpecialPurpose"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(r2))
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with no parent_class relationship"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["NumericFindings", "CategoricFindings", "TextualFindings"]
        MATCH (v2:ActivityInstanceClassValue {name: "Finding"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(r2))
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with no parent_class relationship"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["Events"]
        MATCH (v2:ActivityInstanceClassValue {name: "Event"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(r2))
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with no parent_class relationship"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["Interventions"]
        MATCH (v2:ActivityInstanceClassValue {name: "Intervention"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(r2))
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with no parent_class relationship"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["SpecialPurpose", "Finding", "Event", "Intervention"]
        MATCH (v2:ActivityInstanceClassValue {name: "SubjectObservation"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(r2))
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with no parent_class relationship"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["DeviceSpecialPurpose"]
        MATCH (v2:ActivityInstanceClassValue {name: "Observation"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(r2))
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Instance Classes with no parent_class relationship"""


def test_remove_old_activity_instance_class_nodes():
    logger.info(
        "Check DeviceFinding, DeviceNumericFinding, AssociatedPersonsFinding, Other and OtherQualifiers nodes have been removed"
    )
    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (src:ActivityInstanceClassRoot)--(src_iacv:ActivityInstanceClassValue) 
        WHERE src_iacv.name IN ["DeviceFinding", "DeviceNumericFinding", "AssociatedPersonsFinding", "Other", "OtherQualifiers"]
        RETURN COUNT(*) as count;
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} nodes with label 'DeviceFinding', 'DeviceNumericFinding', 'AssociatedPersonsFinding', 'Other' or 'OtherQualifiers'"""


@pytest.mark.order(after="test_remove_old_activity_instance_class_nodes")
def test_repeat_remove_old_activity_instance_class_nodes(migration):
    assert not migration_011.remove_old_activity_instance_class_nodes(DB_DRIVER, logger)


def test_move_rels_from_old_nodes_to_events_node():
    logger.info("Check all relationships from old nodes have been moved to Events node")
    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (src:ActivityInstanceClassRoot)-[:LATEST]-(src_iacv:ActivityInstanceClassValue) 
        WHERE src_iacv.name IN ["AdverseEvent", "MedicalHistory", "Disposition", "HypoglycaemicEpisode"]
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} nodes with label 'AdverseEvent', 'MedicalHistory', 'Disposition' or 'HypoglycaemicEpisode'"""


@pytest.mark.order(after="test_move_rels_from_old_nodes_to_events_node")
def test_repeat_move_rels_from_old_nodes_to_events_node(migration):
    assert not migration_011.move_rels_from_old_nodes_to_events_node(DB_DRIVER, logger)


def test_move_rels_from_old_nodes_to_interventions_node():
    logger.info(
        "Check all relationships from old nodes have been moved to Interventions node"
    )
    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (src:ActivityInstanceClassRoot)-[:LATEST]-(src_iacv:ActivityInstanceClassValue) 
        WHERE src_iacv.name IN ["CompoundDosing", "ConcomitantMedication"]
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} nodes with label 'CompoundDosing' or 'ConcomitantMedication'"""


@pytest.mark.order(after="test_move_rels_from_old_nodes_to_interventions_node")
def test_repeat_move_rels_from_old_nodes_to_interventions_node(migration):
    assert not migration_011.move_rels_from_old_nodes_to_interventions_node(
        DB_DRIVER, logger
    )


@pytest.mark.order(
    after="test_update_parent_class_relationship_of_activity_instance_class"
)
def test_repeat_update_parent_class_relationship_of_activity_instance_class(migration):
    assert (
        not migration_011.update_parent_class_relationship_of_activity_instance_class(
            DB_DRIVER, logger
        )
    )


def test_update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null():
    logger.info(
        "Check `mandatory` & `is_adam_param_specific_enabled` aren't on nodes and are on relationship"
    )

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:ActivityItem)
        WHERE n.is_adam_param_specific IS NULL
        RETURN COUNT(n) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Item with is_adam_param_specific with NULL"""


@pytest.mark.order(
    after="test_update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null"
)
def test_repeat_update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null(
    migration,
):
    assert not migration_011.update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null(
        DB_DRIVER, logger
    )


def test_move_props_to_has_item_class_rel():
    logger.info(
        "Check `mandatory` & `is_adam_param_specific_enabled` aren't on nodes and are on relationship"
    )

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:ActivityInstanceClassValue)--(:ActivityInstanceClassRoot)-[r:HAS_ITEM_CLASS]-(:ActivityItemClassRoot)--(v1:ActivityItemClassValue)
        WHERE v1.mandatory IS NOT NULL OR v1.is_adam_param_specific_enabled IS NOT NULL
        RETURN COUNT(*) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} Activity Item Class with mandatory or is_adam_param_specific_enabled"""

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:ActivityInstanceClassRoot)-[r:HAS_ITEM_CLASS]-(:ActivityItemClassRoot)
        WHERE r.mandatory IS NULL OR r.is_adam_param_specific_enabled IS NULL
        RETURN COUNT(r) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} HAS_ITEM_CLASS without mandatory or is_adam_param_specific_enabled"""


@pytest.mark.order(after="test_move_props_to_has_item_class_rel")
def test_repeat_move_props_to_has_item_class_rel(migration):
    assert not migration_011.move_props_to_has_item_class_rel(DB_DRIVER, logger)


def test_migrate_data_domain_from_activity_instance_class_to_dataset(migration):
    logger.info(
        "Check Quantity of relationships created for the Domains of Activity Instance Classes"
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        match(a:CTTermRoot)<-[b:HAS_DATA_DOMAIN]-(c:ActivityInstanceClassRoot)
        RETURN distinct a,b,c
        """,
    )
    assert (
        len(records) == 57
    ), "There should exists 57 relationships created, between Activity Instance Classes and Data Domains."


@pytest.mark.order(
    after="test_migrate_data_domain_from_activity_instance_class_to_dataset"
)
def test_repeat_migrate_data_domain_from_activity_instance_class_to_dataset(migration):
    assert (
        not migration_011.migrate_data_domain_from_activity_instance_class_to_dataset(
            DB_DRIVER, logger
        )
    )


def test_migrate_related_codelist_from_activity_item_class_to_codelist(migration):
    logger.info(
        "Check Quantity of relationships created for the Codelists of Activity Item Classes"
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        match(a:ActivityItemClassRoot)-[b:RELATED_CODELIST]->(c:CTCodelistRoot)
        RETURN distinct a,b,c
        """,
    )
    assert len(records) in [
        107,
        111,
    ], "There should exist 107 (when run against db_before_migration_011) or 111 (when run against prd) relationships created, between ActivityItemClass and CTCodelist. Two more than DEV, because there are already created VSCAT codelist and start_datetime, end_datetime, occurrence ACTIVITY ITEMS"


@pytest.mark.order(
    after="test_migrate_related_codelist_from_activity_item_class_to_codelist"
)
def test_repeat_migrate_related_codelist_from_activity_item_class_to_codelist(
    migration,
):
    assert (
        not migration_011.migrate_related_codelist_from_activity_item_class_to_codelist(
            DB_DRIVER, logger
        )
    )


def test_migrate_missings_1(migration):
    logger.info(
        "Test that there are not more ACTIVITY ITEM CLASSES or less ACTIVITY ITEM CLASSES as expected"
    )
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        with ['domain', 'study_id', 'group_id', 'link_id', 'link_group', 'associated_persons_id', 'related_device_id', 'subject_id', 'unique_subject_id', 'related_subject_id', 'reference_id', 'related_domain_abbreviation', 'comment_reference', 'comment', 'evaluator', 'evaluator_id', 'collection_datetime', 'date_of_birth', 'age', 'age_unit', 'sex', 'race', 'ethnicity', 'reference_id', 'term', 'decod', 'continuing', 'start_datetime', 'end_datetime', 'event_category', 'event_subcategory', 'prespecified', 'occurrence', 'completion_status', 'reason_not_done', 'location', 'laterality', 'directionality', 'portion', 'severity', 'serious', 'action_taken', 'causality', 'outcome', 'evaluation_interval', 'ae_number', 'congenital', 'disability', 'death', 'hospitalisation', 'life_threatening', 'toxicity', 'toxicity_grade', 'medically_imp_serious_event', 'reference_id', 'test_code', 'test_name', 'object_of_observation', 'repitition_number', 'test_detail', 'finding_category', 'finding_subcategory', 'position', 'normal_range_lower_limit', 'normal_range_upper_limit', 'normal_range_indicator', 'location', 'laterality', 'directionality', 'portion', 'finding_result_category', 'completion_status', 'reason_not_done', 'vendor_name', 'loinc', 'specimen', 'anatomical_region', 'specimen_condition', 'method', 'analysis_method', 'lead_to_collect_measurement', 'fasting_status', 'evaluator', 'evaluator_id', 'collection_datetime', 'end_datetime', 'time_point', 'elapsed_time', 'evaluation_interval', 'evaluation_interval_text', 'categoric_finding_original_result', 'numeric_finding_original_result', 'numeric_finding_original_result_unit', 'standard_unit', 'unit_dimension', 'textual_finding_original_result', 'reference_id', 'treatment', 'mood', 'intervention_category', 'intervention_subcategory', 'prespecified', 'occurrence', 'completion_status', 'reason_not_done', 'dose', 'dose_description', 'dose_unit', 'dose_form', 'frequency', 'total_daily_dose', 'dose_regimen', 'route', 'location', 'laterality', 'directionality', 'portion', 'lot_number', 'fasting_status', 'start_datetime', 'end_datetime', 'evaluation_interval', 'strength', 'strength_unit', 'reason_for_dose_ajdustment', 'continuing', 'primary_indication', 'prim_indicat_ae_num', 'prim_indicat_mh_num', 'other_indication', 'serial_number', 'device_id_element_short_name', 'device_id_element_name', 'device_id_element_value', 'contact_mode', 'epi_pandemic_change_indicator', 'visit_occurence_reason', 'start_datetime', 'end_datetime', 'description_of_unplanned_visit'] as vec
        unwind vec as vec_unwind
        OPTIONAL MATCH (a:ActivityInstanceClassValue)--(:ActivityInstanceClassRoot)-[r:HAS_ITEM_CLASS]-(v_root:ActivityItemClassRoot)--(c:ActivityItemClassValue)
        WHERE c.name = vec_unwind
        with distinct vec_unwind, count(c) as c_count
        WHERE c_count = 0
        RETURN *
        """,
    )
    resultant_missing_codelists = [record[1] for record in records]
    logger.info(resultant_missing_codelists)
    logger.info(len(records))
    unexpected = []
    expected_missing_codelists = [
        "contact_mode",
        "epi_pandemic_change_indicator",
        "visit_occurence_reason",
        "description_of_unplanned_visit",
    ]
    for expected_missing_codelist in expected_missing_codelists:
        if expected_missing_codelist not in resultant_missing_codelists:
            unexpected.append(expected_missing_codelist)
    assert (
        len(unexpected) == 0
    ), f"{len(unexpected)}  -- UNEXPECTED MISSINGS of needed ACTIVITY ITEM CLASSES"
    logger.info(unexpected)


def test_migrate_missings_2(migration):
    logger.info("Test that there are not more CODELISTs or less CODELISTs as expected")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        with ['DOMAIN', 'MEDEVAL', 'AGEU', 'SEX', 'RACE', 'ETHNIC', 'NCOMPLT', 'NY', 'DECAT', 'CECAT', 'HOCAT', 'MHCAT', 'DSSCAT', 'MHSCAT', 'NY', 'NY', 'ND', 'NY', 'LOC', 'LAT', 'DIR', 'PORTOT', 'AESEV', 'NY', 'ACN', 'OUT', 'NY', 'NY', 'NY', 'NY', 'NY', 'NY', 'DDTESTCD', 'FATESTCD', 'QSTESTCD', 'RPTESTCD', 'RSTESTCD', 'SCTESTCD', 'VSTESTCD', 'ZATESTCD', 'BSTESTCD', 'CVTESTCD', 'DATESTCD', 'DOTESTCD', 'DUTESTCD', 'EGTESTCD', 'FTTESTCD', 'IETESTCD', 'ISTESTCD', 'LBTESTCD', 'MBTESTCD', 'MITESTCD', 'MKTESTCD', 'MOTESTCD', 'MSTESTCD', 'NVTESTCD', 'OETESTCD', 'PCTESTCD', 'PETESTCD', 'PFTESTCD', 'RETESTCD', 'SRTESTCD', 'SSTESTCD', 'TRTESTCD', 'TUTESTCD', 'URTESTCD', 'XATESTCD', 'XSTESTCD', 'ZITESTCD', 'DDTEST', 'FATEST', 'QSTEST', 'RPTEST', 'RSTEST', 'VSTEST', 'ZATEST', 'BSTEST', 'CVTEST', 'DATEST', 'DOTEST', 'DUTEST', 'EGTEST', 'FTTEST', 'IETEST', 'ISTEST', 'LBTEST', 'MBTEST', 'MITEST', 'MKTEST', 'MOTEST', 'MSTEST', 'NVTEST', 'OETEST', 'PCTEST', 'PETEST', 'PFTEST', 'RETEST', 'SRTEST', 'SSTEST', 'TRTEST', 'TUTEST', 'URTEST', 'XATEST', 'XSTEST', 'ZITEST', 'MIFTSDTL', 'QSCAT', 'RPCAT', 'CCCAT', 'VSCAT', 'EGCAT', 'IECAT', 'OECAT', 'PECAT', 'QSCAT', 'RPCAT', 'CCCAT', 'IECAT', 'VSCAT', 'POSITION', 'NRIND', 'LOC', 'LAT', 'DIR', 'PORTOT', 'MSRESCAT', 'ND', 'SPECTYPE', 'GENSMP', 'SPECCOND', 'METHOD', 'EGMETHOD', 'LOC', 'NY', 'EVAL', 'MEDEVAL', 'HEP_CQ', 'QUEST_RESPONSE', 'YESNO', 'UNIT', 'UNIT', 'UNIT_DIMENSION', 'ECTRT', 'EXTRT', 'AGCAT', 'CMCAT', 'ECCAT', 'EXCAT', 'SUCAT', 'MHSCAT', 'DSSCAT', 'NY', 'NY', 'NY', 'UNIT', 'FRM', 'FRQ', 'ROUTE', 'LOC', 'LAT', 'DIR', 'PORTOT', 'NY', 'UNIT', 'NY', 'DIPARMCD', 'DIPARM', 'CNTMODE', 'NY'] as vec
    unwind vec as vec_unwind
    OPTIONAL MATCH (ct:CTCodelistRoot)--(d:CTCodelistAttributesRoot)--(c:CTCodelistAttributesValue)
    WHERE c.submission_value = vec_unwind
    with vec_unwind, count(c) as c_count
    WHERE c_count = 0
    RETURN *
        """,
    )
    resultant_missing_codelists = [record[1] for record in records]
    logger.info(resultant_missing_codelists)
    logger.info(len(records))
    unexpected = []
    expected_missing_codelists = [
        "CECAT",
        "HOCAT",
        "MHCAT",
        "MHSCAT",
        "QSTESTCD",
        "ZATESTCD",
        "FTTESTCD",
        "IETESTCD",
        "MKTESTCD",
        "PCTESTCD",
        "PETESTCD",
        "URTESTCD",
        "XATESTCD",
        "XSTESTCD",
        "ZITESTCD",
        "QSTEST",
        "ZATEST",
        "FTTEST",
        "IETEST",
        "MKTEST",
        "PCTEST",
        "PETEST",
        "URTEST",
        "XATEST",
    ]

    for expected_missing_codelist in expected_missing_codelists:
        if expected_missing_codelist not in resultant_missing_codelists:
            unexpected.append(expected_missing_codelist)
    assert (
        len(unexpected) == 0
    ), f"{len(unexpected)} - not exepected missing CODELISTs or less CODELISTs as expected"
    logger.info(unexpected)


def test_migrate_missings_3(migration):
    logger.info(
        "Check Quantity of missings CODELISTs needed on the Wizard Stepper ActivityInstanceClass"
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        WITH ['AE','AG','APAE','APCE','APCM','APDD','APDM','APFACE','APHO','APMH','APQS','APRP','APRS','APSC','APVS','APZA','CE','CM','CO','CV','DA','DD','DE','DI','DM','DO','DR','DS','DT','DU','DV','DX','EC','EG','EX','FA','FAXB','FT','HO','IE','IS','LB','MB','MH','MI','ML','MO','MS','OE','PC','PE','PF','PP','PR','QS','RE','RP','RS','SC','SE','SR','SS','SU','SV','TA','TD','TE','TI','TR','TS','TU','TV','VS','XA','XB','XH','XR','XS','ZA','ZE','ZL','ZV'] AS vec
        unwind vec as vec_unwind

        OPTIONAL MATCH (codelist:CTCodelistRoot)--(cttermroot:CTTermRoot)--(cttermattroot:CTTermAttributesRoot)-[:LATEST]-(cttermattvalue:CTTermAttributesValue)
                    WHERE  cttermattvalue.code_submission_value = vec_unwind and codelist.uid = "C66734" or codelist.uid = "C111113"
        with vec_unwind, count(cttermattvalue) as c_count
        WHERE c_count = 0
        RETURN *
        """,
    )
    logger.info([record[1] for record in records])
    logger.info(len(records))
    assert (
        len(records) == 0
    ), f"{len(records)} - Quantity of missings CODELISTs needed on the Wizard Stepper ActivityInstanceClass"


def test_migrate_missings_4(migration):
    logger.info("Check Quantity of missings ALL NEEDED ACTIVITY INSTANCE CLASSES  ")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        WITH ['Event','Intervention','Event','Event','Intervention','Finding','SpecialPurpose','Finding','Event','Event','Finding','Finding','Finding','Finding','Finding','Finding','Event','Intervention','SpecialPurpose','Finding','Finding','Finding','Event','DeviceSpecialPurpose','SpecialPurpose','Finding','Event','Event','Finding','Event','Intervention','Intervention','Finding','Intervention','Finding','Finding','Finding','Event','Finding','Finding','Finding','Finding','Event','Finding','Intervention','Finding','Finding','Finding','Finding','Finding','Finding','Finding','Intervention','Finding','Finding','Finding','Finding','Finding','Finding','Finding','Intervention','SpecialPurpose','Finding','Finding','Finding','Finding','Event','Event','Event','Finding','Finding','Intervention','Finding','Finding']
        AS vec
        unwind vec as vec_unwind
        WITH tolower(vec_unwind) as vec_unwind_lower
        OPTIONAL MATCH (ainstcv:ActivityInstanceClassValue)-[:LATEST]-(ainstcr:ActivityInstanceClassRoot)
            WHERE  tolower(ainstcv.name) = vec_unwind_lower 
        with vec_unwind_lower, count(ainstcv) as c_count
        WHERE c_count = 0
        RETURN *
        """,
    )
    logger.info([record[1] for record in records])
    logger.info(len(records))
    assert (
        len(records) == 0
    ), f"{len(records)} -Check Quantity of missings ALL NEEDED ACTIVITY INSTANCE CLASSES"


def test_migrate_missings_5(migration):
    logger.info(
        "SPECIFIC NUMERIC FINDINGS ------- UNEXPECTED MISSINGS on the needed ACTIVITY ITEM CLASSES specific for FINDINGS AND NUMERIC FINDINGS"
    )
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        WITH ['numeric_finding_original_result','numeric_finding_original_result_unit','standard_unit','unit_dimension','reference_id','test_code','test_name','object_of_observation','repitition_number','test_detail','finding_category','finding_subcategory','position','normal_range_lower_limit','normal_range_upper_limit','normal_range_indicator','location','laterality','directionality','portion','finding_result_category','completion_status','reason_not_done','vendor_name','loinc','specimen','anatomical_region','specimen_condition','method','analysis_method','lead_to_collect_measurement','fasting_status','evaluator','evaluator_id','collection_datetime','end_datetime','time_point','elapsed_time','evaluation_interval','evaluation_interval_text'] as vec

        unwind vec as vec_unwind
        OPTIONAL MATCH (a:ActivityInstanceClassValue)--(:ActivityInstanceClassRoot)-[r:HAS_ITEM_CLASS]-(v_root:ActivityItemClassRoot)--(c:ActivityItemClassValue)
        WHERE c.name = vec_unwind and (tolower(a.name) = "numericfindings" or tolower(a.name) = "finding")
        with distinct vec_unwind, count(c) as c_count
        WHERE c_count = 0
        RETURN *
        """,
    )
    resultant_missing_codelists = [record[1] for record in records]
    logger.info(resultant_missing_codelists)
    logger.info(len(records))
    unexpected = []
    # list of missing that are expected to be missing
    expected_missing_codelists = (
        []
    )  # IN PRD ALL THE CODELISTS EXISTS, THERE ARE NO EXPECTED MISSINGS, NOT FUTURE MIGRATION

    for expected_missing_codelist in expected_missing_codelists:
        if expected_missing_codelist not in resultant_missing_codelists:
            unexpected.append(expected_missing_codelist)
    assert (
        len(unexpected) == 0
    ), f"{len(unexpected)}   SPECIFIC NUMERIC FINDINGS ------- UNEXPECTED MISSINGS on the needed ACTIVITY ITEM CLASSES specific for FINDINGS AND NUMERIC FINDINGS"
    logger.info(unexpected)


def test_migrate_missings_6(migration):
    logger.info(
        " CORRECTIONS CSV ---- Number of nodes already created specified on the corrections csv  "
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        // creation
        with [
            ["LEVEL_2_CLASS", "SpecialPurpose", "SpecialPurpose"],
            ["LEVEL_2_CLASS", "Finding", "Finding"],
            ["LEVEL_2_CLASS", "Event", "Event"],
            ["LEVEL_2_CLASS", "Intervention", "Intervention"],
            ["LEVEL_2_CLASS", "DeviceFinding", "NumericFindings"],
            ["LEVEL_2_CLASS", "AssociatedPersonsFinding", "REMOVED"],
            ["LEVEL_2_CLASS", "APEvent", "REMOVED"],
            ["LEVEL_2_CLASS", "APIntervention", "REMOVED"],
            ["LEVEL_2_CLASS", "Other", "REMOVED"],
            ["LEVEL_2_CLASS", "DOES NOT EXIST", "DeviceSpecialPurpose"],
            ["LEVEL_3_CLASS", "Demographics", "Demographics"],
            ["LEVEL_3_CLASS", "Comments", "Comments"],
            ["LEVEL_3_CLASS", "NumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "CategoricFinding", "CategoricFindings"],
            ["LEVEL_3_CLASS", "TextualFinding", "TextualFindings"],
            ["LEVEL_3_CLASS", "AdverseEvent", "Events"],
            ["LEVEL_3_CLASS", "MedicalHistory", "Events"],
            ["LEVEL_3_CLASS", "Disposition", "Events"],
            ["LEVEL_3_CLASS", "HypoglycaemicEpisode", "Events"],
            ["LEVEL_3_CLASS", "CompoundDosing", "Interventions"],
            ["LEVEL_3_CLASS", "ConcomitantMedication", "Interventions"],
            ["LEVEL_3_CLASS", "DeviceNumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "APNumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "APCategoricFinding", "CategoricFindings"],
            ["LEVEL_3_CLASS", "APTextualFinding", "TextualFindings"],
            ["LEVEL_3_CLASS", "APAdverseEvent", "Events"],
            ["LEVEL_3_CLASS", "APAdverseEventProduct", "REMOVED"],
            ["LEVEL_3_CLASS", "APMedicalHistory", "Events"],
            ["LEVEL_3_CLASS", "APCompoundDosing", "Interventions"],
            ["LEVEL_3_CLASS", "APConcomitantMedication", "Interventions"],
            ["LEVEL_3_CLASS", "OtherQualifiers", "REMOVED"],
            ["LEVEL_3_CLASS", "DOES NOT EXIST", "DeviceIdentifiers"]
        ] as data_correction
        unwind data_correction as data_correction_unw
        WITH data_correction_unw[2] as name_to_create
            where
                (data_correction_unw[1]<>data_correction_unw[2])  // There's no difference no no need to change
                and (not data_correction_unw[2] = "REMOVED") // not to be removed
                and ( data_correction_unw[1] = "DOES NOT EXIST") // These cases

        OPTIONAL MATCH (aicr:ActivityInstanceClassRoot)-[:LATEST]-(aicv:ActivityInstanceClassValue)
        where aicv.name = name_to_create
        return  aicv.name as already_created
        """,
    )
    logger.info([record[0] for record in records])
    assert (
        len(records) == 2
    ), f"{len(records)} -  CORRECTIONS CSV ---- Number of nodes already created specified on the corrections csv"


def test_migrate_missings_7(migration):
    logger.info(
        "CORRECTIONS CSV ---- Number of nodes to REMOVE specified on the corrections csv "
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        // MODIFY
        with [
            ["LEVEL_2_CLASS", "SpecialPurpose", "SpecialPurpose"],
            ["LEVEL_2_CLASS", "Finding", "Finding"],
            ["LEVEL_2_CLASS", "Event", "Event"],
            ["LEVEL_2_CLASS", "Intervention", "Intervention"],
            ["LEVEL_2_CLASS", "DeviceFinding", "NumericFindings"],
            ["LEVEL_2_CLASS", "AssociatedPersonsFinding", "REMOVED"],
            ["LEVEL_2_CLASS", "APEvent", "REMOVED"],
            ["LEVEL_2_CLASS", "APIntervention", "REMOVED"],
            ["LEVEL_2_CLASS", "Other", "REMOVED"],
            ["LEVEL_2_CLASS", "DOES NOT EXIST", "DeviceSpecialPurpose"],
            ["LEVEL_3_CLASS", "Demographics", "Demographics"],
            ["LEVEL_3_CLASS", "Comments", "Comments"],
            ["LEVEL_3_CLASS", "NumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "CategoricFinding", "CategoricFindings"],
            ["LEVEL_3_CLASS", "TextualFinding", "TextualFindings"],
            ["LEVEL_3_CLASS", "AdverseEvent", "Events"],
            ["LEVEL_3_CLASS", "MedicalHistory", "Events"],
            ["LEVEL_3_CLASS", "Disposition", "Events"],
            ["LEVEL_3_CLASS", "HypoglycaemicEpisode", "Events"],
            ["LEVEL_3_CLASS", "CompoundDosing", "Interventions"],
            ["LEVEL_3_CLASS", "ConcomitantMedication", "Interventions"],
            ["LEVEL_3_CLASS", "DeviceNumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "APNumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "APCategoricFinding", "CategoricFindings"],
            ["LEVEL_3_CLASS", "APTextualFinding", "TextualFindings"],
            ["LEVEL_3_CLASS", "APAdverseEvent", "Events"],
            ["LEVEL_3_CLASS", "APAdverseEventProduct", "REMOVED"],
            ["LEVEL_3_CLASS", "APMedicalHistory", "Events"],
            ["LEVEL_3_CLASS", "APCompoundDosing", "Interventions"],
            ["LEVEL_3_CLASS", "APConcomitantMedication", "Interventions"],
            ["LEVEL_3_CLASS", "OtherQualifiers", "REMOVED"],
            ["LEVEL_3_CLASS", "DOES NOT EXIST", "DeviceIdentifiers"]
        ] as data_correction
        unwind data_correction as data_correction_unw
        OPTIONAL MATCH (aicv:ActivityInstanceClassValue)-[:LATEST]-(:ActivityInstanceClassRoot)
            where aicv.name = data_correction_unw[1] 
                and (data_correction_unw[1]<>data_correction_unw[2])  // There's no difference no no need to change
                and ( data_correction_unw[2] = "REMOVED") // These need to be removed in another query
                and (not data_correction_unw[1] = "DOES NOT EXIST") // These need to be created in another query
        RETURN collect(distinct aicv.name) AS to_remove
        """,
    )
    logger.info([record[1] for record in records])
    logger.info(len(records[0][0]))
    assert (
        len(records[0][0]) == 0
    ), f"{len(records[0][0])} -  CORRECTIONS CSV ---- Number of nodes to REMOVE specified on the corrections csv "


def test_migrate_missings_8(migration):
    logger.info(
        "CORRECTIONS CSV ---- Number of nodes to MODIFY specified on the corrections csv  "
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        with [
            ["LEVEL_2_CLASS", "SpecialPurpose", "SpecialPurpose"],
            ["LEVEL_2_CLASS", "Finding", "Finding"],
            ["LEVEL_2_CLASS", "Event", "Event"],
            ["LEVEL_2_CLASS", "Intervention", "Intervention"],
            ["LEVEL_2_CLASS", "DeviceFinding", "NumericFindings"],
            ["LEVEL_2_CLASS", "AssociatedPersonsFinding", "REMOVED"],
            ["LEVEL_2_CLASS", "APEvent", "REMOVED"],
            ["LEVEL_2_CLASS", "APIntervention", "REMOVED"],
            ["LEVEL_2_CLASS", "Other", "REMOVED"],
            ["LEVEL_2_CLASS", "DOES NOT EXIST", "DeviceSpecialPurpose"],
            ["LEVEL_3_CLASS", "Demographics", "Demographics"],
            ["LEVEL_3_CLASS", "Comments", "Comments"],
            ["LEVEL_3_CLASS", "NumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "CategoricFinding", "CategoricFindings"],
            ["LEVEL_3_CLASS", "TextualFinding", "TextualFindings"],
            ["LEVEL_3_CLASS", "AdverseEvent", "Events"],
            ["LEVEL_3_CLASS", "MedicalHistory", "Events"],
            ["LEVEL_3_CLASS", "Disposition", "Events"],
            ["LEVEL_3_CLASS", "HypoglycaemicEpisode", "Events"],
            ["LEVEL_3_CLASS", "CompoundDosing", "Interventions"],
            ["LEVEL_3_CLASS", "ConcomitantMedication", "Interventions"],
            ["LEVEL_3_CLASS", "DeviceNumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "APNumericFinding", "NumericFindings"],
            ["LEVEL_3_CLASS", "APCategoricFinding", "CategoricFindings"],
            ["LEVEL_3_CLASS", "APTextualFinding", "TextualFindings"],
            ["LEVEL_3_CLASS", "APAdverseEvent", "Events"],
            ["LEVEL_3_CLASS", "APAdverseEventProduct", "REMOVED"],
            ["LEVEL_3_CLASS", "APMedicalHistory", "Events"],
            ["LEVEL_3_CLASS", "APCompoundDosing", "Interventions"],
            ["LEVEL_3_CLASS", "APConcomitantMedication", "Interventions"],
            ["LEVEL_3_CLASS", "OtherQualifiers", "REMOVED"],
            ["LEVEL_3_CLASS", "DOES NOT EXIST", "DeviceIdentifiers"]
        ] as data_correction
        unwind data_correction as data_correction_unw

        MATCH (aicv:ActivityInstanceClassValue)-[:LATEST]-(:ActivityInstanceClassRoot)
            where aicv.name = data_correction_unw[1] 
                and (data_correction_unw[1]<>data_correction_unw[2])  // There's no difference no no need to change
                and (not data_correction_unw[2] = "REMOVED") // These need to be removed in another query
                and (not data_correction_unw[1] = "DOES NOT EXIST") // These need to be created in another query
        // SET aicv.name = data_correction_unw[2]
        RETURN collect(distinct aicv.name) AS changed
        """,
    )
    logger.info([record[1] for record in records])
    logger.info(len(records[0][0]))
    assert (
        len(records[0][0]) == 0
    ), f"{len(records[0][0])} CORRECTIONS CSV ---- Number of nodes to MODIFY specified on the corrections csv "


def test_migrate_soa_group_activity_group_activity_subgroup_activity_orders(migration):
    logger.info(
        "Check StudySoAGroup, StudyActivityGroup, StudyActivitySubGroup and StudyActivity order numbers assignment"
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
        WHERE NOT (study_activity)-[:BEFORE]-() AND (study_soa_group.order=null OR study_activity_group.order=null OR study_activity_subgroup.order=null OR study_activity.order=null)
        RETURN *
        """,
    )
    assert (
        len(records) == 0
    ), f"Found some last version of StudySoAGroup/StudyActivityGroup/StudyActivitySubGroup/StudyActivity {records} without order assigned"

    # calling for Studies by the API as it will exclude Deleted Studies
    payload = api_get_paged(
        "/studies",
        params={
            "total_count": True,
            "sort_by": json.dumps({"uid": True}),
        },
    )
    studies = payload["items"]
    for study in studies:
        study_uid = study["uid"]

        logger.info(
            "Verifying that orders are properly assigned in the following Study (%s)",
            study_uid,
        )
        # Call endpoint to check API response which is asserted under the hood
        study_activities = api_get_paged(
            f"/studies/{study_uid}/study-activities", page_size=10
        )["items"]
        for study_activity in study_activities:
            assert study_activity["order"] is not None
            assert study_activity["study_soa_group"]["order"] is not None
            if (
                study_activity["study_activity_group"]["study_activity_group_uid"]
                is not None
            ):
                assert study_activity["study_activity_group"]["order"] is not None
            if (
                study_activity["study_activity_subgroup"]["study_activity_subgroup_uid"]
                is not None
            ):
                assert study_activity["study_activity_subgroup"]["order"] is not None


@pytest.mark.order(
    after="test_migrate_soa_group_activity_group_activity_subgroup_activity_orders"
)
def test_repeat_migrate_soa_group_activity_group_activity_subgroup_activity_orders(
    migration,
):
    assert not migration_011.migrate_soa_group_activity_group_activity_subgroup_activity_orders(
        DB_DRIVER, logger
    )
