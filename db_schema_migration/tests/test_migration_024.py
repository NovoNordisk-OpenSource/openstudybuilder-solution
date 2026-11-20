import contextlib
import json
import os

import pytest

from migrations import migration_024
from migrations.utils.utils import (
    api_get,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.utils.utils import clear_db

try:
    from tests.data.db_before_migration_024 import TEST_DATA
except ImportError:
    TEST_DATA = ""


db = get_db_connection()
DB_DRIVER = get_db_driver()
logger = get_logger(os.path.basename(__file__))

# Cypher condition telling whether the StudyVisit bound to `sv` has the Early discontinuation visit type
IS_ED_VISIT_TYPE_CONDITION = """EXISTS {
    MATCH (sv)-[:HAS_VISIT_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)
          -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(:CTTermNameValue {name: 'Early discontinuation'})
}"""

# Properties of a StudyVisit bound to `sv` that the SPECIAL_VISIT migration must leave untouched
SPECIAL_VISIT_PROPERTIES_RETURN = """
OPTIONAL MATCH (sv)-[:HAS_VISIT_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(vt:CTTermRoot)
WITH sv, collect(vt.uid) AS visit_type_uids
RETURN elementId(sv) AS element_id,
       visit_type_uids,
       sv.visit_sublabel_reference AS visit_sublabel_reference
"""


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def special_visits_before_migration(initial_data):
    """Snapshot of the properties of SPECIAL_VISIT nodes that the migration must not change"""
    records, _ = run_cypher_query(
        DB_DRIVER,
        f"""
        MATCH (sv:StudyVisit {{visit_class: 'SPECIAL_VISIT'}})
        {SPECIAL_VISIT_PROPERTIES_RETURN}
        """,
    )
    return {r["element_id"]: dict(r) for r in records}


@pytest.fixture(scope="module")
def odm_items_with_datatype_before_migration(initial_data):
    """Element ids and legacy datatype of OdmItemValue nodes, excluding 'comment'"""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (oiv:OdmItemValue)
        WHERE oiv.datatype IS NOT NULL
          AND NOT toLower(oiv.datatype) = 'comment'
        RETURN elementId(oiv) AS element_id, oiv.datatype AS datatype
        """,
    )
    return {r["element_id"]: r["datatype"] for r in records}


@pytest.fixture(scope="module")
def migration(
    initial_data,
    special_visits_before_migration,
    odm_items_with_datatype_before_migration,
):
    # Run migration
    migration_024.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_uppercase_project_numbers(migration):
    logger.info("Verifying uppercase_project_number results")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (p:Project) WHERE p.project_number IS NOT NULL and p.project_number <> toUpper(p.project_number)
        RETURN COUNT(p) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "All Project nodes must have uppercase project_number property after migration"


@pytest.mark.order(after="test_uppercase_project_numbers")
def test_repeat_uppercase_project_numbers(migration):
    assert not migration_024.uppercase_project_numbers(DB_DRIVER, logger)


def test_change_catalogue_of_datatype_codelist(migration):
    logger.info("Verifying change_catalogue_of_datatype_codelist results")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (cc:CTCatalogue)-[:HAS_CODELIST]->(ccr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
        (:CTCodelistAttributesRoot)-[:LATEST]->(cca:CTCodelistAttributesValue)
        WHERE cca.submission_value = "DATATYPE"
        RETURN cc.name AS catalogue_name
        """,
    )
    for record in records:
        assert (
            record["catalogue_name"] == "DDF CT"
        ), "CTCodelist with DATATYPE submission value must be linked to DDF CT catalogue"


def test_datatype_codelist_exists(migration):
    """Test data is expected to contain a DATATYPE codelist — guards against fixture regressions."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (ccr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
        (:CTCodelistAttributesRoot)-[:LATEST]->(cca:CTCodelistAttributesValue)
        WHERE cca.submission_value = "DATATYPE"
        RETURN COUNT(ccr) AS count
        """,
    )
    assert (
        records[0]["count"] == 1
    ), "Expected exactly one CTCodelist with DATATYPE submission value in test data"


@pytest.mark.order(after="test_change_catalogue_of_datatype_codelist")
def test_repeat_change_catalogue_of_datatype_codelist(migration):
    assert not migration_024.change_catalogue_of_datatype_codelist(DB_DRIVER, logger)


def test_codelist_name_values_have_properties(migration):
    """All CTCodelistNameValue nodes must have is_ordinal and codelist_type after migration."""
    logger.info("Verifying CTCodelistNameValue nodes have is_ordinal and codelist_type")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (nv:CTCodelistNameValue)
        WHERE nv.is_ordinal IS NULL OR nv.codelist_type IS NULL
        RETURN count(nv) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "All CTCodelistNameValue nodes must have is_ordinal and codelist_type after migration"


def test_codelist_attributes_values_cleaned(migration):
    """No CTCodelistAttributesValue should still have is_ordinal or codelist_type."""
    logger.info(
        "Verifying CTCodelistAttributesValue nodes have no is_ordinal or codelist_type"
    )
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (av:CTCodelistAttributesValue)
        WHERE av.is_ordinal IS NOT NULL OR av.codelist_type IS NOT NULL
        RETURN count(av) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "No CTCodelistAttributesValue should have is_ordinal or codelist_type after migration"


def test_codelist_properties_copied_correctly(migration):
    """Verify the actual values were copied from the LATEST attributes value."""
    logger.info("Verifying property values on CTCodelistNameValue nodes")

    # Codelist 1: had is_ordinal=true, codelist_type='Extensible' — all name versions should have those
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:CTCodelistRoot {uid: 'ct_codelist_root_1'})-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
        RETURN DISTINCT nv.uid AS uid, nv.is_ordinal AS is_ordinal, nv.codelist_type AS codelist_type
        ORDER BY nv.uid
        """,
    )
    assert len(records) == 2, "Expected 2 name value versions for codelist 1"
    for record in records:
        assert record["is_ordinal"] is True
        assert record["codelist_type"] == "Extensible"

    # Codelist 2: had no properties on attributes — should get defaults
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:CTCodelistRoot {uid: 'ct_codelist_root_2'})-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
        RETURN DISTINCT nv.uid AS uid, nv.is_ordinal AS is_ordinal, nv.codelist_type AS codelist_type
        """,
    )
    assert len(records) == 1, "Expected 1 name value version for codelist 2"
    assert records[0]["is_ordinal"] is False
    assert records[0]["codelist_type"] == "Standard"


@pytest.mark.order(after="test_codelist_properties_copied_correctly")
def test_repeat_move_codelist_properties(migration):
    assert not migration_024.move_codelist_properties_to_name_value(DB_DRIVER, logger)


# Codelists from tests/data/db_before_migration_024.py's STRESC_CODELIST block, keyed by
# CTCodelistRoot.uid, with the expected ordinal (float) per CTCodelistTerm.submission_value.
# C182521 (KFSS108) has an "Unknown" term, which is expected to resolve to ordinal None since
# it can't be parsed as an integer.
STRESC_CODELIST_TERM_ORDINALS = {
    "C182508": {"0": 0.0, "1": 1.0, "2": 2.0},  # ATLAS101 TN/TC
    "C182509": {"0": 0.0, "2": 2.0},  # ATLAS102 TN/TC
    "C182521": {"0": 0.0, "1": 1.0, "Unknown": None},  # KFSS108 TN/TC
}

# Codelists in the same test data whose name does NOT contain STRESC; this migration step
# must leave them untouched.
NON_STRESC_CODELIST_UIDS = ["C141656", "C141657"]

# Codelist whose name DOES contain STRESC, but none of its terms have an integer-like
# submission_value ("i0".."i4"); this migration step must NOT mark it ordinal, nor set
# ordinal on any of its HAS_TERM relationships.
STRESC_CODELIST_WITHOUT_INTEGER_TERMS_UID = "C190904"


@pytest.mark.order(after="test_repeat_move_codelist_properties")
def test_set_ordinal_for_stresc_codelists(migration):
    """Generic checks, safe to run against any migrated database (no codelist uids).

    A STRESC codelist with at least one integer-like term must be flagged is_ordinal, and
    for every ordinal STRESC codelist the HAS_TERM.ordinal of each term must reflect the
    term's submission_value when it's an integer, or be unset otherwise.
    """
    logger.info("Verifying set_ordinal_for_stresc_codelists results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (cr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
        WHERE nv.name CONTAINS 'STRESC'
          AND coalesce(nv.is_ordinal, false) = false
          AND EXISTS {
              MATCH (cr)-[:HAS_TERM]->(ct:CTCodelistTerm)
              WHERE toInteger(ct.submission_value) IS NOT NULL
          }
        RETURN collect(DISTINCT cr.uid)[..10] AS uids
        """,
    )
    assert not records[0][
        "uids"
    ], f"STRESC codelists with integer-like terms must be flagged is_ordinal: {records[0]['uids']}"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (cr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
        WHERE nv.name CONTAINS 'STRESC' AND nv.is_ordinal = true
        WITH DISTINCT cr
        MATCH (cr)-[ht:HAS_TERM]->(ct:CTCodelistTerm)
        WITH cr, ct, ht, toFloat(toInteger(ct.submission_value)) AS expected
        WHERE (ht.ordinal IS NULL) <> (expected IS NULL) OR ht.ordinal <> expected
        RETURN cr.uid AS uid, ct.submission_value AS submission_value, ht.ordinal AS ordinal
        LIMIT 10
        """,
    )
    assert not records, (
        "HAS_TERM.ordinal of ordinal STRESC codelists must match the integer "
        f"submission_value of the term, mismatches: {[dict(r) for r in records]}"
    )


@pytest.mark.order(after="test_set_ordinal_for_stresc_codelists")
def test_set_ordinal_for_stresc_codelists_fixture_data(migration):
    """Uses fixture-specific data (codelist uids) — not reused by verification_024."""
    for codelist_uid, expected_ordinals in STRESC_CODELIST_TERM_ORDINALS.items():
        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
            RETURN DISTINCT nv.is_ordinal AS is_ordinal
            """,
            {"uid": codelist_uid},
        )
        assert records, f"Expected name value version(s) for codelist '{codelist_uid}'"
        assert all(
            record["is_ordinal"] is True for record in records
        ), f"All name value versions of '{codelist_uid}' must be flagged is_ordinal"

        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (:CTCodelistRoot {uid: $uid})-[ht:HAS_TERM]->(ct:CTCodelistTerm)
            RETURN ct.submission_value AS submission_value, ht.ordinal AS ordinal
            """,
            {"uid": codelist_uid},
        )
        ordinals_by_submval = {
            record["submission_value"]: record["ordinal"] for record in records
        }
        assert ordinals_by_submval == expected_ordinals, (
            f"Unexpected term ordinals for codelist '{codelist_uid}': "
            f"{ordinals_by_submval}"
        )


@pytest.mark.order(after="test_set_ordinal_for_stresc_codelists_fixture_data")
def test_non_stresc_codelists_not_marked_ordinal(migration):
    """Generic check, safe to run against any migrated database (no codelist uids).

    A codelist that is neither a STRESC codelist nor flagged ordinal must not have
    ordinal set on any of its HAS_TERM relationships.
    """
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (cr:CTCodelistRoot)
        WHERE NOT EXISTS {
            MATCH (cr)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
            WHERE nv.name CONTAINS 'STRESC' OR nv.is_ordinal = true
        }
        MATCH (cr)-[ht:HAS_TERM]->()
        WHERE ht.ordinal IS NOT NULL
        RETURN collect(DISTINCT cr.uid)[..10] AS uids
        """,
    )
    assert not records[0]["uids"], (
        "Non-STRESC, non-ordinal codelists must not have ordinal set on their terms: "
        f"{records[0]['uids']}"
    )


@pytest.mark.order(after="test_non_stresc_codelists_not_marked_ordinal")
def test_non_stresc_codelists_not_marked_ordinal_fixture_data(migration):
    """Uses fixture-specific data (codelist uids) — not reused by verification_024."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:CTCodelistRoot {uid: 'ct_codelist_root_2'})-[:HAS_NAME_ROOT]->
              (:CTCodelistNameRoot)-[:LATEST]->(nv:CTCodelistNameValue)
        RETURN nv.is_ordinal AS is_ordinal
        """,
    )
    assert records[0]["is_ordinal"] is False

    for codelist_uid in NON_STRESC_CODELIST_UIDS:
        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
            RETURN DISTINCT nv.is_ordinal AS is_ordinal
            """,
            {"uid": codelist_uid},
        )
        assert records, f"Expected name value version(s) for codelist '{codelist_uid}'"
        assert all(
            record["is_ordinal"] is False for record in records
        ), f"Non-STRESC codelist '{codelist_uid}' must not be flagged is_ordinal"

        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (:CTCodelistRoot {uid: $uid})-[ht:HAS_TERM]->(:CTCodelistTerm)
            RETURN ht.ordinal AS ordinal
            """,
            {"uid": codelist_uid},
        )
        assert (
            records
        ), f"Expected HAS_TERM relationship(s) for codelist '{codelist_uid}'"
        assert all(
            record["ordinal"] is None for record in records
        ), f"Non-STRESC codelist '{codelist_uid}' must not have ordinal set on its terms"


@pytest.mark.order(after="test_non_stresc_codelists_not_marked_ordinal_fixture_data")
def test_stresc_codelist_without_integer_terms_not_marked_ordinal(migration):
    """Uses fixture-specific data (codelist uids) — not reused by verification_024.

    A codelist whose name contains STRESC but none of whose terms have an integer-like
    submission_value must NOT be flagged ordinal, nor have ordinal set on its HAS_TERM
    relationships."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
        RETURN DISTINCT nv.is_ordinal AS is_ordinal
        """,
        {"uid": STRESC_CODELIST_WITHOUT_INTEGER_TERMS_UID},
    )
    assert records, (
        f"Expected name value version(s) for codelist "
        f"'{STRESC_CODELIST_WITHOUT_INTEGER_TERMS_UID}'"
    )
    assert all(record["is_ordinal"] is False for record in records), (
        f"STRESC codelist '{STRESC_CODELIST_WITHOUT_INTEGER_TERMS_UID}' without integer "
        "terms must not be flagged is_ordinal"
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:CTCodelistRoot {uid: $uid})-[ht:HAS_TERM]->(ct:CTCodelistTerm)
        RETURN ct.submission_value AS submission_value, ht.ordinal AS ordinal
        """,
        {"uid": STRESC_CODELIST_WITHOUT_INTEGER_TERMS_UID},
    )
    assert records, (
        f"Expected HAS_TERM relationship(s) for codelist "
        f"'{STRESC_CODELIST_WITHOUT_INTEGER_TERMS_UID}'"
    )
    assert all(record["ordinal"] is None for record in records), (
        f"STRESC codelist '{STRESC_CODELIST_WITHOUT_INTEGER_TERMS_UID}' without integer "
        f"terms must not have ordinal set on its terms, got "
        f"{ {r['submission_value']: r['ordinal'] for r in records} }"
    )


@pytest.mark.order(
    after="test_stresc_codelist_without_integer_terms_not_marked_ordinal"
)
def test_repeat_set_ordinal_for_stresc_codelists(migration):
    assert not migration_024.set_ordinal_for_stresc_codelists(DB_DRIVER, logger)


def test_archived_library(migration):
    """Archived library must exist in the graph and via the libraries API."""
    logger.info("Verifying Archived library")
    query = """
    MATCH (n:Library {name: "Archived"})
    RETURN n
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 1, "Archived library must exist in the graph"

    libs = api_get("/libraries").json()
    archived = [lib for lib in libs if lib["name"] == "Archived"]
    assert len(archived) == 1, "Archived library must exist in the libraries API"
    assert archived[0]["is_editable"] is False


@pytest.mark.order(after="test_archived_library")
def test_repeat_ensure_archived_library(migration):
    assert not migration_024.ensure_archived_library(logger)


def test_migrate_feature_flags_to_root_value(migration):
    """Verify FeatureFlag nodes migrate to the Root/Value model."""
    logger.info("Verify FeatureFlag Root/Value migration")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:FeatureFlag)
        RETURN count(n) AS count
        """,
    )
    assert records[0]["count"] == 0, "All flat FeatureFlag nodes must be deleted"

    root_records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:FeatureFlagRoot)
        RETURN count(root) AS count
        """,
    )
    if root_records[0]["count"] == 0:
        return

    complete_records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:FeatureFlagRoot)
        MATCH (root)-[:LATEST]->(value:FeatureFlagValue)
        MATCH (root)-[:LATEST_FINAL]->(value)
        MATCH (root)-[hv:HAS_VERSION]->(value)
        WHERE hv.end_date IS NULL
          AND hv.status = 'Final'
          AND hv.version IS NOT NULL
          AND root.uid STARTS WITH 'FeatureFlag_'
          AND value.section IN ['admin', 'library', 'nullable', 'studies']
          AND value.feature IS NOT NULL
          AND value.enabled IN [true, false]
        RETURN count(root) AS count
        """,
    )
    assert root_records[0]["count"] == complete_records[0]["count"], (
        "FeatureFlagRoot count must match the number of roots with the complete "
        "LATEST/LATEST_FINAL/HAS_VERSION Final structure"
    )


@pytest.mark.order(after="test_migrate_feature_flags_to_root_value")
def test_repeat_migrate_feature_flags_to_root_value(migration):
    """Ensure rerunning the feature flag migration is idempotent."""
    assert not migration_024.migrate_feature_flags_to_root_value(DB_DRIVER, logger)


@pytest.mark.order(after="test_repeat_migrate_feature_flags_to_root_value")
def test_recover_from_partial_failure_state(migration):
    """Ensure the migration recovers when legacy and migrated nodes coexist."""
    run_cypher_query(
        DB_DRIVER,
        """
                UNWIND [
                    {
                        sn: 999,
                        section: 'admin',
                        feature: 'Demo Feature',
                        name: 'demo_flag',
                        enabled: true,
                        description: 'Demo description'
                    },
                    {
                        sn: 1000,
                        section: 'studies',
                        feature: 'Studies Feature',
                        name: 'studies_flag',
                        enabled: false,
                        description: null
                    }
                ] AS flag
                CREATE (:FeatureFlag {
                    sn: flag.sn,
                    section: flag.section,
                    feature: flag.feature,
                    name: flag.name,
                    enabled: flag.enabled,
                    description: flag.description
                })
        """,
    )

    # This mimics a safe-abort/crash state where old and migrated representations coexist.
    assert migration_024.migrate_feature_flags_to_root_value(DB_DRIVER, logger)

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:FeatureFlag)
        RETURN count(n) AS count
        """,
    )
    assert records[0]["count"] == 0

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue {name: 'demo_flag'})
        RETURN count(root) AS count
        """,
    )
    assert records[0]["count"] == 1


def test_link_sponsor_model_values_to_library(migration):
    """Verify every SponsorModelValue node is linked to the 'Sponsor' Library."""
    logger.info("Verify SponsorModelValue -> Library migration")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (value:SponsorModelValue)
        WHERE NOT EXISTS { MATCH (:Library)-[:CONTAINS_SPONSOR_MODEL]->(value) }
        RETURN count(value) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "Every SponsorModelValue must be linked to a Library"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (library:Library {name: 'Sponsor'})-[:CONTAINS_SPONSOR_MODEL]->(value:SponsorModelValue)
        RETURN count(value) AS count
        """,
    )
    assert records[0]["count"] > 0, "Expected at least one migrated SponsorModelValue"


@pytest.mark.order(after="test_link_sponsor_model_values_to_library")
def test_repeat_link_sponsor_model_values_to_library(migration):
    """Ensure rerunning the sponsor model library link migration is idempotent."""
    assert not migration_024.link_sponsor_model_values_to_library(DB_DRIVER, logger)


@pytest.mark.order(after="test_repeat_link_sponsor_model_values_to_library")
def test_recover_from_partial_link_state(migration):
    """Ensure the migration only links the nodes that are still missing a Library."""
    run_cypher_query(
        DB_DRIVER,
        """
        MATCH (ig:DataModelIGRoot)-[:HAS_VERSION]->(dm:DataModelIGValue)
        WITH dm LIMIT 1
        CREATE (v:SponsorModelValue {name: 'partial_state_sponsor_model'})
        CREATE (v)-[:EXTENDS_VERSION]->(dm)
        """,
    )

    # This mimics a safe-abort/crash state where some SponsorModelValue nodes
    # are already linked and some are not.
    assert migration_024.link_sponsor_model_values_to_library(DB_DRIVER, logger)

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (value:SponsorModelValue)
        WHERE NOT EXISTS { MATCH (:Library)-[:CONTAINS_SPONSOR_MODEL]->(value) }
        RETURN count(value) AS count
        """,
    )
    assert records[0]["count"] == 0

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (library:Library {name: 'Sponsor'})-[:CONTAINS_SPONSOR_MODEL]->
              (value:SponsorModelValue {name: 'partial_state_sponsor_model'})
        RETURN count(value) AS count
        """,
    )
    assert records[0]["count"] == 1


def test_link_dataset_variable_to_data_model_catalogue(migration):
    """Verify every DatasetVariable -> DataModelCatalogue link exists."""
    logger.info("Verify DatasetVariable -> DataModelCatalogue migration")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (dv:DatasetVariable) WHERE NOT EXISTS { (dv)<-[:HAS_DATASET_VARIABLE]-(dm:DataModelCatalogue) }
        RETURN count(dv) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "Expected all DatasetVariable nodes to be linked to at least one DataModelCatalogue"


@pytest.mark.order(after="test_link_dataset_variable_to_data_model_catalogue")
def test_repeat_link_dataset_variable_to_data_model_catalogue(migration):
    """Ensure rerunning the DatasetVariable -> DataModelCatalogue migration is idempotent."""
    assert not migration_024.link_dataset_variable_to_data_model_catalogue(
        DB_DRIVER, logger
    )


def test_remove_ct_config_nodes(migration):
    logger.info("Verifying remove_ct_config_nodes results")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n) WHERE n:CTConfigRoot OR n:CTConfigValue
        RETURN COUNT(n) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "All CTConfigRoot and CTConfigValue nodes must be removed after migration"


@pytest.mark.order(after="test_remove_ct_config_nodes")
def test_repeat_remove_ct_config_nodes(migration):
    assert not migration_024.remove_ct_config_nodes(DB_DRIVER, logger)


def test_migrate_meta_study_fields(migration):
    """MetaStudyField nodes exist and are linked to a SEMTCDT term.

    Step 7 creates nothing when the SEMTCDT codelist is missing, and step 8 then removes its source.
    """
    logger.info("Verifying migrate_meta_study_fields results")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (msf:MetaStudyField)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
              -[:HAS_SELECTED_TERM]->(ctr:CTTermRoot)
              <-[:HAS_TERM_ROOT]-(:CTCodelistTerm)
              <-[:HAS_TERM]-(:CTCodelistRoot)
              -[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
              -[:LATEST]->(:CTCodelistAttributesValue {submission_value: $codelist_submval})
        RETURN count(DISTINCT msf) AS count
        """,
        params={"codelist_submval": migration_024.SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL},
    )
    assert (
        records[0]["count"] > 0
    ), "MetaStudyField nodes linked to a SEMTCDT term must exist after migration"


# Non-null study fields of the CT_CONFIGS block in tests/data/db_before_migration_024.py,
# with the SEMTCDT term their study_field_data_type maps to
CT_CONFIG_STUDY_FIELD_SEMANTIC_DATA_TYPES = {
    "study_type_code": "text",
    "is_extension_trial": "boolean",
    "therapeutic_area_codes": "ctTerm",
    "intervention_type_code": "text",
    "is_trial_randomised": "boolean",
    "ct_gov_id": "text",
    "study_number": "text",
}


@pytest.mark.order(after="test_migrate_meta_study_fields")
def test_migrate_meta_study_fields_fixture_data(migration):
    """Uses fixture-specific data (study field names) — not reused by verification_024."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (msf:MetaStudyField)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
              -[:HAS_SELECTED_TERM]->(ctr:CTTermRoot)<-[:HAS_TERM_ROOT]-(clt:CTCodelistTerm)
        WHERE msf.osb_field_name IN $field_names
        RETURN msf.osb_field_name AS field_name, clt.submission_value AS semantic_data_type
        """,
        params={"field_names": list(CT_CONFIG_STUDY_FIELD_SEMANTIC_DATA_TYPES)},
    )
    semantic_data_types = {r["field_name"]: r["semantic_data_type"] for r in records}
    assert semantic_data_types == CT_CONFIG_STUDY_FIELD_SEMANTIC_DATA_TYPES


@pytest.mark.order(after="test_migrate_meta_study_fields_fixture_data")
def test_repeat_migrate_meta_study_fields(migration):
    assert not migration_024.migrate_meta_study_fields(DB_DRIVER, logger)


@pytest.mark.order(after="test_repeat_migrate_meta_study_fields")
def test_check_datatype_codelists_passes_on_migrated_db(migration):
    """A repeated run on a migrated database must not be blocked by the prerequisite check."""
    migration_024.check_datatype_codelists(DB_DRIVER, logger)


@contextlib.contextmanager
def _hidden_codelist(codelist_submval: str):
    """Temporarily rename the codelist's submission value, as if it were not loaded."""
    hidden_submval = f"{codelist_submval}_HIDDEN_BY_TEST"
    query = """
        MATCH (clav:CTCodelistAttributesValue {submission_value: $from_submval})
        SET clav.submission_value = $to_submval
        """
    run_cypher_query(
        DB_DRIVER,
        query,
        params={"from_submval": codelist_submval, "to_submval": hidden_submval},
    )
    try:
        yield
    finally:
        run_cypher_query(
            DB_DRIVER,
            query,
            params={"from_submval": hidden_submval, "to_submval": codelist_submval},
        )


@pytest.mark.order(after="test_check_datatype_codelists_passes_on_migrated_db")
def test_missing_semantic_data_type_codelist_stops_migration(migration):
    """Without SEMTCDT the migration fails, and the CTConfig nodes are kept for a re-run."""
    run_cypher_query(
        DB_DRIVER,
        """
        CREATE (:CTConfigValue {study_field_name: 'test_missing_semtcdt',
                                study_field_data_type: 'text'})
        """,
    )
    try:
        with _hidden_codelist(migration_024.SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL):
            with pytest.raises(RuntimeError, match="SEMTCDT"):
                migration_024.check_datatype_codelists(DB_DRIVER, logger)
            with pytest.raises(RuntimeError, match="SEMTCDT"):
                migration_024.migrate_meta_study_fields(DB_DRIVER, logger)
            with pytest.raises(RuntimeError, match="test_missing_semtcdt"):
                migration_024.remove_ct_config_nodes(DB_DRIVER, logger)

        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (cv:CTConfigValue {study_field_name: 'test_missing_semtcdt'})
            RETURN count(cv) AS count
            """,
        )
        assert records[0]["count"] == 1, "CTConfigValue must not be removed"
    finally:
        run_cypher_query(
            DB_DRIVER,
            """
            MATCH (n)
            WHERE (n:CTConfigValue AND n.study_field_name = 'test_missing_semtcdt')
               OR (n:MetaStudyField AND n.osb_field_name = 'test_missing_semtcdt')
            DETACH DELETE n
            """,
        )


@pytest.mark.order(after="test_missing_semantic_data_type_codelist_stops_migration")
def test_missing_odm_data_type_codelist_stops_migration(migration):
    run_cypher_query(
        DB_DRIVER,
        "CREATE (:OdmItemValue {name: 'test_missing_codmdt', datatype: 'string'})",
    )
    try:
        with _hidden_codelist(migration_024.DATATYPE_CODELIST_SUBMVAL):
            with pytest.raises(RuntimeError, match="CODMDT"):
                migration_024.check_datatype_codelists(DB_DRIVER, logger)
    finally:
        run_cypher_query(
            DB_DRIVER,
            "MATCH (oiv:OdmItemValue {name: 'test_missing_codmdt'}) DETACH DELETE oiv",
        )


# Sponsor model names from
# import_sponsor_data/datafiles/sponsor_library/sponsormodel/*/model_info.json,
# and the field-schema version each declares. The test data's
# LIBRARY_SPONSOR_MODEL block creates a SponsorModelValue for each of these
# names, so the migration can resolve them by name alone (no CSV/dataset data
# needed).
SPONSOR_MODEL_SCHEMA_VERSIONS = {
    "sdtmig_mastermodel_3.2_NN15": 1,
    "sdtmig_mastermodel_3.3_NN01": 2,
    "sdtmig_mastermodel_3.3_NN02": 2,
    "sdtmig_mastermodel_3.3_NN03": 2,
}


def test_load_sponsor_model_schemas(migration):
    """Verify every Sponsor Model field-schema version on disk got published."""
    logger.info("Verify Sponsor Model field-schema publication")

    published = api_get(
        "/standards/sponsor-models/schema", params={"library_name": "Sponsor"}
    ).json()
    published_versions = {item["schema_version"] for item in published}

    expected_versions = set(SPONSOR_MODEL_SCHEMA_VERSIONS.values())
    assert expected_versions <= published_versions, (
        f"Expected schema versions {sorted(expected_versions)} to be published, "
        f"found {sorted(published_versions)}"
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:SponsorModelSchemaRoot {uid: 'SponsorModelSchema_Sponsor'})
              -[:HAS_SCHEMA_VERSION]->(value:SponsorModelSchemaValue)
        RETURN value.schema_version AS schema_version
        ORDER BY schema_version
        """,
    )
    graph_versions = {record["schema_version"] for record in records}
    assert expected_versions <= graph_versions, (
        f"Expected SponsorModelSchemaValue nodes for versions "
        f"{sorted(expected_versions)}, found {sorted(graph_versions)}"
    )


@pytest.mark.order(after="test_load_sponsor_model_schemas")
def test_repeat_load_sponsor_model_schemas(migration):
    """Ensure re-publishing already-published schema versions is a no-op."""
    assert not migration_024.load_sponsor_model_schemas(logger)


@pytest.mark.order(after="test_load_sponsor_model_schemas")
def test_link_sponsor_model_values_to_schema(migration):
    """Verify every known SponsorModelValue follows the schema version its model_info.json declares."""
    logger.info("Verify SponsorModelValue -> SponsorModelSchemaValue migration")

    for sponsor_model_name, schema_version in SPONSOR_MODEL_SCHEMA_VERSIONS.items():
        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (value:SponsorModelValue {name: $name})
                  -[:FOLLOWS_SCHEMA]->(schema_value:SponsorModelSchemaValue)
            RETURN schema_value.schema_version AS schema_version
            """,
            {"name": sponsor_model_name},
        )
        assert (
            records
        ), f"SponsorModelValue '{sponsor_model_name}' must have a FOLLOWS_SCHEMA link"
        assert records[0]["schema_version"] == schema_version, (
            f"SponsorModelValue '{sponsor_model_name}' must follow schema version "
            f"{schema_version}, found {records[0]['schema_version']}"
        )


@pytest.mark.order(after="test_link_sponsor_model_values_to_schema")
def test_repeat_link_sponsor_model_values_to_schema(migration):
    """Ensure rerunning the sponsor model schema link migration is idempotent."""
    assert not migration_024.link_sponsor_model_values_to_schema(DB_DRIVER, logger)


# ── SPECIAL_VISIT → SINGLE_VISIT class change ────────────────────────────────


def test_no_special_visit_nodes_remain(migration):
    """No StudyVisit should have visit_class='SPECIAL_VISIT' after migration."""
    logger.info("Verifying no SPECIAL_VISIT nodes remain")
    records, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (sv:StudyVisit {visit_class: 'SPECIAL_VISIT'}) RETURN count(sv) AS cnt",
    )
    assert (
        records[0]["cnt"] == 0
    ), "All SPECIAL_VISIT nodes must be converted to SINGLE_VISIT"


@pytest.mark.order(after="test_no_special_visit_nodes_remain")
def test_repeat_change_visit_class_to_single(migration):
    """change_visit_class_to_single is idempotent — second run makes no updates."""
    assert not migration_024.change_visit_class_to_single(DB_DRIVER, logger)


# ── visit_suffix assignment ───────────────────────────────────────────────────


def test_suffix_matches_short_visit_label(migration):
    """visit_suffix must equal the last character of short_visit_label for all converted visits."""
    logger.info("Verifying visit_suffix matches right(short_visit_label, 1)")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyVisit {visit_class: 'SINGLE_VISIT'})
        WHERE sv.visit_suffix IS NOT NULL
          AND sv.short_visit_label IS NOT NULL
          AND sv.visit_suffix <> right(sv.short_visit_label, 1)
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "visit_suffix must equal the last character of short_visit_label"


def test_non_ed_suffix_letters(migration):
    """Non-ED converted visits must not use X, Y, or Z as suffix — those are ED-only letters."""
    logger.info("Verifying non-ED suffix letters are not X, Y, Z")
    records, _ = run_cypher_query(
        DB_DRIVER,
        f"""
        MATCH (sv:StudyVisit {{visit_class: 'SINGLE_VISIT'}})
        WHERE sv.visit_suffix IS NOT NULL
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
          AND NOT {IS_ED_VISIT_TYPE_CONDITION}
          AND sv.visit_suffix IN ['X', 'Y', 'Z']
        RETURN count(sv) AS cnt
        """,
    )
    assert records[0]["cnt"] == 0, (
        "Non-ED suffix visits must not use letters X, Y, Z — "
        "if this fails, short_visit_label contains an unexpected suffix for a non-ED visit"
    )


# ── visit type and visit_sublabel_reference untouched ─────────────────────────


def test_converted_visits_keep_visit_type_and_anchor(
    migration, special_visits_before_migration
):
    """Converted visits keep their visit type and visit_sublabel_reference."""
    logger.info(
        "Verifying converted visits keep visit type and visit_sublabel_reference"
    )
    assert (
        special_visits_before_migration
    ), "Test data is expected to contain SPECIAL_VISIT nodes"
    records, _ = run_cypher_query(
        DB_DRIVER,
        f"""
        MATCH (sv:StudyVisit) WHERE elementId(sv) IN $element_ids
        {SPECIAL_VISIT_PROPERTIES_RETURN}
        """,
        {"element_ids": list(special_visits_before_migration)},
    )
    after = {r["element_id"]: dict(r) for r in records}
    assert after == special_visits_before_migration


def test_suffix_visits_keep_visit_sublabel_reference(migration):
    """Converted visits keep referencing the old anchor visit via visit_sublabel_reference."""
    logger.info("Verifying suffix visits keep visit_sublabel_reference")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyVisit {visit_class: 'SINGLE_VISIT'})
        WHERE sv.visit_suffix IS NOT NULL
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
          AND sv.visit_sublabel_reference IS NULL
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "All suffix visits must keep visit_sublabel_reference"


def test_ed_suffix_visits_have_no_expected_time_value(migration):
    """Converted Early discontinuation visits don't get expected_time_value, they take place at the timing of their parent visit."""
    logger.info("Verifying ED suffix visits have no expected_time_value")
    records, _ = run_cypher_query(
        DB_DRIVER,
        f"""
        MATCH (sv:StudyVisit {{visit_class: 'SINGLE_VISIT'}})
        WHERE sv.visit_suffix IS NOT NULL
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
          AND {IS_ED_VISIT_TYPE_CONDITION}
          AND sv.expected_time_value IS NOT NULL
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "ED suffix visits must not have expected_time_value set"


def test_non_ed_suffix_visits_have_expected_time_value(migration):
    """Converted visits other than Early discontinuation get expected_time_value, so they don't land at day 0.

    Only current visits of the latest study version have an anchor timing to take it from.
    """
    logger.info("Verifying non-ED suffix visits have expected_time_value")
    records, _ = run_cypher_query(
        DB_DRIVER,
        f"""
        MATCH (:StudyRoot)-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit {{visit_class: 'SINGLE_VISIT'}})
        WHERE NOT (study_value)<-[:BEFORE]-(:Delete)
          AND NOT (sv)<-[:BEFORE]-(:StudyAction)
          AND sv.visit_suffix IS NOT NULL
          AND NOT {IS_ED_VISIT_TYPE_CONDITION}
          AND sv.expected_time_value IS NULL
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "Non-ED suffix visits must have expected_time_value set to the timing of their anchor visit"


# ── HAS_TIMEPOINT → 0 days / Global anchor visit ─────────────────────────────


def test_all_suffix_visits_have_timepoint(migration):
    """Every converted visit must have a HAS_TIMEPOINT relationship."""
    logger.info("Verifying HAS_TIMEPOINT is set on all suffix visits")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyVisit {visit_class: 'SINGLE_VISIT'})
        WHERE sv.visit_suffix IS NOT NULL
          AND NOT (sv)-[:HAS_TIMEPOINT]->()
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "All suffix visits must have a HAS_TIMEPOINT relationship"


def test_all_converted_visit_nodes_have_timepoint(
    migration, special_visits_before_migration
):
    """Every former SPECIAL_VISIT node gets the timepoint, also the nodes of visits deleted since a locked study version."""
    logger.info("Verifying HAS_TIMEPOINT is set on all former SPECIAL_VISIT nodes")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyVisit) WHERE elementId(sv) IN $element_ids
          AND NOT (sv)-[:HAS_TIMEPOINT]->()
        RETURN count(sv) AS cnt
        """,
        {"element_ids": list(special_visits_before_migration)},
    )
    assert (
        records[0]["cnt"] == 0
    ), "All former SPECIAL_VISIT nodes must have a HAS_TIMEPOINT relationship"


def test_suffix_visit_timepoints_are_zero_global_anchor(migration):
    """All suffix visit timepoints must be 0 (any unit) from Global anchor visit."""
    logger.info("Verifying suffix visit timepoints are 0 / Global anchor")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyVisit {visit_class: 'SINGLE_VISIT'})
        WHERE sv.visit_suffix IS NOT NULL
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
        MATCH (sv)-[:HAS_TIMEPOINT]->(tp:TimePointRoot)-[:LATEST]->(tpv:TimePointValue)
        MATCH (tpv)-[:HAS_VALUE]->(:NumericValueRoot)-[:LATEST]->(nv:NumericValue)
        MATCH (tpv)-[:HAS_TIME_REFERENCE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ref:CTTermRoot)
        MATCH (ref)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(ref_name:CTTermNameValue)
        WHERE NOT (nv.value = 0.0 AND ref_name.name = 'Global anchor visit')
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "All suffix visit timepoints must be 0 from Global anchor visit"


# ── no unwanted timing nodes ──────────────────────────────────────────────────


def test_suffix_visits_have_no_study_day_nodes(migration):
    """Converted visits must not have HAS_STUDY_DAY — their timing comes from the visit they reference."""
    logger.info("Verifying suffix visits have no StudyDay nodes")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyVisit {visit_class: 'SINGLE_VISIT'})
        WHERE sv.visit_suffix IS NOT NULL
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
        MATCH (sv)-[:HAS_STUDY_DAY]->()
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "Converted visits must not have HAS_STUDY_DAY relationships"


def test_suffix_visits_have_no_study_duration_days_nodes(migration):
    """Converted visits must not have HAS_STUDY_DURATION_DAYS — their timing comes from the visit they reference."""
    logger.info("Verifying suffix visits have no StudyDurationDays nodes")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sv:StudyVisit {visit_class: 'SINGLE_VISIT'})
        WHERE sv.visit_suffix IS NOT NULL
          AND NOT (sv)<-[:HAS_STUDY_VISIT]-(:StudyValue)<-[:BEFORE]-(:Delete)
        MATCH (sv)-[:HAS_STUDY_DURATION_DAYS]->()
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "Converted visits must not have HAS_STUDY_DURATION_DAYS relationships"


def test_migrating_marker_cleaned_up(migration):
    """The temporary _migrating property must be removed from all nodes after migration."""
    logger.info("Verifying _migrating marker is cleaned up")
    records, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (sv:StudyVisit) WHERE sv._migrating IS NOT NULL RETURN count(sv) AS cnt",
    )
    assert (
        records[0]["cnt"] == 0
    ), "All _migrating markers must be removed after migration"


# ── visit_order assignment ────────────────────────────────────────────────────


def test_all_current_visits_have_visit_order(migration):
    """Every current StudyVisit reachable from a LATEST study must have order set.
    Orphaned visit nodes (not connected to any study) are excluded — assign_visit_order
    only processes visits reachable via the LATEST study path."""
    logger.info("Verifying order is set on all current StudyVisit nodes")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sr:StudyRoot)-[:LATEST]->(study_val:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit)
        WHERE NOT (study_val)<-[:BEFORE]-(:Delete)
          AND NOT (sv)<-[:BEFORE]-(:StudyAction)
          AND sv.order IS NULL
        RETURN count(sv) AS cnt
        """,
    )
    assert (
        records[0]["cnt"] == 0
    ), "All current StudyVisit nodes reachable from LATEST must have order set after migration"


def test_visit_order_is_non_negative(migration):
    """order must be >= 0 for all current StudyVisit nodes.
    0 is valid for information visits (settings.visit_0_number = 0)."""
    logger.info("Verifying order >= 0 on all current StudyVisit nodes")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sr:StudyRoot)-[:LATEST]->(study_val:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit)
        WHERE NOT (study_val)<-[:BEFORE]-(:Delete)
          AND NOT (sv)<-[:BEFORE]-(:StudyAction)
          AND sv.order IS NOT NULL
          AND sv.order < 0
        RETURN count(sv) AS cnt
        """,
    )
    assert records[0]["cnt"] == 0, "order must be >= 0 for all current StudyVisit nodes"


def test_visit_order_unique_per_study(migration):
    """Within each study, no two current visits may share the same order value."""
    logger.info("Verifying order is unique within each study")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (sr:StudyRoot)-[:LATEST]->(study_val:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit)
        WHERE NOT (study_val)<-[:BEFORE]-(:Delete)
          AND NOT (sv)<-[:BEFORE]-(:StudyAction)
        WITH sr.uid AS study_uid, sv.order AS order_val, count(*) AS cnt
        WHERE cnt > 1
        RETURN count(*) AS duplicate_count
        """,
    )
    assert records[0]["duplicate_count"] == 0, "order must be unique within each study"


@pytest.mark.order(after="test_all_current_visits_have_visit_order")
def test_assign_visit_order_idempotent(migration):
    """assign_visit_order can be re-run (no studies → no API calls → no updates)."""
    # On a DB without studies assign_visit_order short-circuits and returns False.
    # On a DB with studies it raises if the API fails for any of them.
    result = migration_024.assign_visit_order(DB_DRIVER, logger)
    # On an empty test DB there is nothing to update, so the return must be False.
    records, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (sr:StudyRoot)-[:LATEST]->(study_val:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit) WHERE NOT (study_val)<-[:BEFORE]-(:Delete) AND NOT (sv)<-[:BEFORE]-(:StudyAction) RETURN count(sv) AS cnt",
    )
    has_visits = records[0]["cnt"] > 0
    if not has_visits:
        assert (
            result is False
        ), "assign_visit_order must return False when there are no visits"


def test_no_odm_item_has_datatype_string_property(migration):
    """
    After migration, no OdmItemValue node should retain the legacy datatype string property.
    """
    logger.info("Verifying no OdmItemValue nodes have datatype string property")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (oiv:OdmItemValue)
        WHERE oiv.datatype IS NOT NULL
        RETURN oiv.datatype AS datatype, count(oiv) AS count
        """,
    )
    assert not records, (
        "No OdmItemValue nodes should have the datatype string property after migration, "
        "values without a matching term in the CODMDT codelist: "
        f"{ {record['datatype']: record['count'] for record in records} }"
    )


def test_odm_item_has_no_data_type_relationship_for_comment_and_text(migration):
    """
    No OdmItemValue node should have a HAS_DATA_TYPE relationship for the "comment"
    or "text" datatype after migration.
    """
    logger.info("Verifying OdmItemValue nodes have HAS_DATA_TYPE relationships")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:OdmItemValue)-[:HAS_DATA_TYPE]->(:CTTermContext)
            -[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(clt:CTCodelistTerm)
        WHERE toLower(clt.submission_value) IN ['comment', 'text']
        RETURN count(clt) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "No OdmItemValue may have a 'comment' or 'text' data type after migration"


def test_odm_items_with_other_datatypes_have_data_type_relationship(
    migration, odm_items_with_datatype_before_migration
):
    """
    Every OdmItemValue whose legacy datatype was neither "comment" must
    now have a HAS_DATA_TYPE relationship to the matching CODMDT term.

    When called from the verification module the pre-migration snapshot is not
    available (None), so only the resulting state is checked.
    """
    if odm_items_with_datatype_before_migration is None:
        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (oiv:OdmItemValue)
            WHERE oiv.datatype IS NOT NULL
              AND NOT toLower(oiv.datatype) = 'comment'
              AND NOT (oiv)-[:HAS_DATA_TYPE]->(:CTTermContext)
            RETURN count(oiv) AS count
            """,
        )
        assert (
            records[0]["count"] == 0
        ), "OdmItemValue nodes with a legacy datatype lack a HAS_DATA_TYPE relationship"
        return
    assert (
        odm_items_with_datatype_before_migration
    ), "Test data must contain OdmItemValue nodes with datatypes other than comment"
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        UNWIND $element_ids AS element_id
        MATCH (oiv:OdmItemValue) WHERE elementId(oiv) = element_id
        OPTIONAL MATCH (oiv)-[:HAS_DATA_TYPE]->(:CTTermContext)
            -[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(clt:CTCodelistTerm)
        RETURN element_id, collect(toLower(clt.submission_value)) AS submission_values
        """,
        params={"element_ids": list(odm_items_with_datatype_before_migration)},
    )
    actual = {r["element_id"]: r["submission_values"] for r in records}
    missing = {
        element_id: datatype
        for element_id, datatype in odm_items_with_datatype_before_migration.items()
        if datatype.lower() not in actual.get(element_id, [])
    }
    assert not missing, f"OdmItemValue nodes without HAS_DATA_TYPE: {missing}"


def test_ct_term_context_linked_to_codelist(migration):
    """
    CTTermContext nodes created by the migration must be linked to the CODMDT codelist.
    """
    logger.info("Verifying CTTermContext nodes are linked to the CODMDT codelist")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (oiv:OdmItemValue)-[:HAS_DATA_TYPE]->(ctx:CTTermContext)
        WHERE NOT EXISTS {
            (ctx)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)
            -[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
            -[:LATEST]->(clav:CTCodelistAttributesValue)
            WHERE clav.submission_value = $codelist_submval
        }
        RETURN count(DISTINCT ctx) AS count
        """,
        params={"codelist_submval": migration_024.DATATYPE_CODELIST_SUBMVAL},
    )
    assert (
        records[0]["count"] == 0
    ), "All CTTermContext nodes of ODM Item datatype must be linked to CODMDT codelist"


@pytest.mark.order(after="test_no_odm_item_has_datatype_string_property")
def test_repeat_migrate_odm_item_datatype(migration):
    """Re-running the first migration step must be idempotent (no updates)."""
    assert not migration_024.migrate_odm_item_datatype_to_ct_term(DB_DRIVER, logger)


@pytest.mark.order(after="test_no_odm_item_has_datatype_string_property")
def test_repeat_remove_datatype_string_property(migration):
    """Re-running the property removal step must be idempotent (no updates)."""
    assert not migration_024.remove_odm_item_datatype_string_property(DB_DRIVER, logger)


def test_remove_unit_definition_deprecated_properties(migration):
    logger.info("Verifying remove_unit_definition_deprecated_properties results")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.si_unit IS NOT NULL OR u.legacy_code IS NOT NULL
        RETURN COUNT(u) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "No UnitDefinitionValue node must have si_unit or legacy_code after migration"


def test_unit_definitions_exist(migration):
    """Test data is expected to contain four UnitDefinitionValue nodes — guards against fixture regressions."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:UnitDefinitionRoot)-->(u:UnitDefinitionValue)
        WHERE root.uid IN ['Unit_000001', 'Unit_000002', 'Unit_000003', 'Unit_000004']
        RETURN COUNT(DISTINCT u) AS count
        """,
    )
    assert (
        records[0]["count"] == 4
    ), "Expected exactly four UnitDefinitionValue nodes in test data"


@pytest.mark.order(after="test_remove_unit_definition_deprecated_properties")
def test_repeat_remove_unit_definition_deprecated_properties(migration):
    assert not migration_024.remove_unit_definition_deprecated_properties(
        DB_DRIVER, logger
    )


def test_reset_conversion_factor_for_non_convertible_units(migration):
    logger.info("Verifying reset_conversion_factor_for_non_convertible_units results")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.convertible_unit = false
          AND u.master_unit = false
          AND u.conversion_factor_to_master IS NOT NULL
        RETURN COUNT(u) AS count
        """,
    )
    assert records[0]["count"] == 0, (
        "No non-convertible, non-master UnitDefinitionValue node must have a "
        "conversion_factor_to_master after migration"
    )


def test_reset_conversion_factor_keeps_master_unit_factor(migration):
    """Uses fixture-specific data — not reused by verification_024."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:UnitDefinitionRoot {uid: 'Unit_000004'})-[:LATEST]->(u:UnitDefinitionValue)
        RETURN u.conversion_factor_to_master AS conversion_factor_to_master
        """,
    )
    assert (
        records[0]["conversion_factor_to_master"] == 1.0
    ), "Non-convertible master unit must keep its conversion_factor_to_master"


@pytest.mark.order(after="test_reset_conversion_factor_for_non_convertible_units")
def test_repeat_reset_conversion_factor_for_non_convertible_units(migration):
    assert not migration_024.reset_conversion_factor_for_non_convertible_units(
        DB_DRIVER, logger
    )


def test_migrate_control_type_to_array_field(migration):
    """Generic checks, safe to run against any migrated database.

    CONTROL_TYPE_STUDY_FIELDS seeds one field per conversion branch (term
    linked, null flavor only, value without a term link) plus an audit trail
    entry, so each rule below is exercised by the test data.
    """
    logger.info("Verifying migrate_control_type_to_array_field results")
    params = {
        "old_field_name": migration_024.CONTROL_TYPE_OLD_FIELD_NAME,
        "new_field_name": migration_024.CONTROL_TYPE_NEW_FIELD_NAME,
    }

    def assert_no_matches(query: str, message: str) -> None:
        records, _ = run_cypher_query(DB_DRIVER, query, params)
        assert records[0]["count"] == 0, message

    assert_no_matches(
        """
        MATCH (sf:StudyField {field_name: $old_field_name})
        RETURN count(sf) AS count
        """,
        "No StudyField, including audit-trail-only ones, may keep the"
        " single-select 'control_type_code' field name",
    )
    assert_no_matches(
        """
        MATCH (sf:StudyField {field_name: $new_field_name})
        WHERE sf:StudyTextField
           OR NOT sf:StudyArrayField
           OR NOT apoc.meta.cypher.isType(sf.value, "LIST OF STRING")
           OR EXISTS { (:StudyValue)-[:HAS_TEXT_FIELD]->(sf) }
        RETURN count(sf) AS count
        """,
        "Every 'control_type_codes' StudyField must be a StudyArrayField with a list"
        " value, linked from StudyValue via HAS_ARRAY_FIELD only",
    )
    assert_no_matches(
        """
        MATCH (sf:StudyArrayField {field_name: $new_field_name})
              -[:HAS_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(term:CTTermRoot)
        WITH sf, collect(DISTINCT term.uid) AS term_uids
        WHERE apoc.coll.sort(term_uids) <> apoc.coll.sort(sf.value)
        RETURN count(sf) AS count
        """,
        "A term-linked 'control_type_codes' value must hold exactly its linked term uids",
    )
    assert_no_matches(
        """
        MATCH (sf:StudyArrayField {field_name: $new_field_name})
        WHERE size(sf.value) > 0
          AND EXISTS { (sf)-[:HAS_REASON_FOR_NULL_VALUE]->() }
        RETURN count(sf) AS count
        """,
        "A 'control_type_codes' field with a null flavor must have an empty value",
    )
    assert_no_matches(
        """
        MATCH (sf:StudyArrayField {field_name: $new_field_name})
        WHERE size(sf.value) = 0
          AND NOT EXISTS { (sf)-[:HAS_REASON_FOR_NULL_VALUE]->() }
        RETURN count(sf) AS count
        """,
        "Every 'control_type_codes' field must keep either a value or a null flavor;"
        " an empty one means a stored value was dropped",
    )
    assert_no_matches(
        """
        MATCH (msf:MetaStudyField {osb_field_name: $old_field_name})
        RETURN count(msf) AS count
        """,
        "MetaStudyField 'control_type_code' must be renamed to 'control_type_codes'",
    )
    assert_no_matches(
        """
        MATCH (tsp:CTTermNameValue)-[:RELATED_STUDY_FIELD_SELECTION]->
              (:MetaStudyField {osb_field_name: $new_field_name})
        WHERE tsp.cardinality IS NOT NULL AND tsp.cardinality <> 'Many'
        RETURN count(tsp) AS count
        """,
        "The Control Type TS parameter must have cardinality 'Many'",
    )


@pytest.mark.order(after="test_migrate_control_type_to_array_field")
def test_repeat_migrate_control_type_to_array_field(migration):
    assert not migration_024.migrate_control_type_to_array_field(DB_DRIVER, logger)


def test_rename_activity_item_class_display_name_to_label(migration):
    logger.info("Verifying rename_activity_item_class_display_name_to_label results")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v:ActivityItemClassValue)
        WHERE v.display_name IS NOT NULL
        RETURN COUNT(v) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "No ActivityItemClassValue node must have display_name after migration"


def test_activity_item_class_labels_copied_correctly(migration):
    """Uses fixture-specific data — not reused by verification_024."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:ActivityItemClassRoot)-[hv:HAS_VERSION]->(v:ActivityItemClassValue)
        RETURN root.uid AS uid, hv.version AS version, v.label AS label
        """,
    )
    labels = {(record["uid"], record["version"]): record["label"] for record in records}
    assert labels == {
        # All versions are renamed, not only LATEST
        ("ActivityItemClass_000001", "1.0"): "Domain v1",
        ("ActivityItemClass_000001", "2.0"): "Domain",
        # No display_name to rename, no label created
        ("ActivityItemClass_000002", "1.0"): None,
        # NonStandardVariableValue nodes are renamed as well
        ("ActivityItemClass_000003", "0.1"): "Non-standard variable",
        # An existing label is not overwritten
        ("ActivityItemClass_000004", "1.0"): "Test name",
    }


@pytest.mark.order(after="test_activity_item_class_labels_copied_correctly")
def test_repeat_rename_activity_item_class_display_name_to_label(migration):
    assert not migration_024.rename_activity_item_class_display_name_to_label(
        DB_DRIVER, logger
    )


def test_convert_non_string_short_visit_labels(migration):
    """No Non or Unscheduled StudyVisit node has a non-string short_visit_label."""
    logger.info(
        "Verify short_visit_label values of Non and Unscheduled visits are strings"
    )

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (visit:StudyVisit)
        WHERE visit.visit_class IN ['NON_VISIT', 'UNSCHEDULED_VISIT']
            AND visit.short_visit_label IS NOT NULL
            AND NOT visit.short_visit_label IS :: STRING
        RETURN visit.uid AS uid, visit.short_visit_label AS short_visit_label
        """,
    )
    assert (
        not records
    ), f"StudyVisit nodes with non-string short_visit_label: {[record.data() for record in records]}"


def test_convert_non_string_short_visit_labels_values(migration):
    """Uses fixture-specific data — not reused by verification_024."""
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (visit:StudyVisit)
        WHERE visit.uid STARTS WITH 'StudyVisit_INT_' OR visit.uid STARTS WITH 'StudyVisit_STR_'
        RETURN visit.uid AS uid, visit.short_visit_label AS short_visit_label
        """,
    )
    assert {record["uid"]: record["short_visit_label"] for record in records} == {
        "StudyVisit_INT_NON": "V29999",
        "StudyVisit_INT_UNSCHEDULED": "V29500",
        "StudyVisit_INT_SINGLE": 7,
        "StudyVisit_STR_NON": "V29999",
    }


@pytest.mark.order(after="test_convert_non_string_short_visit_labels")
def test_repeat_convert_non_string_short_visit_labels(migration):
    assert not migration_024.convert_non_string_short_visit_labels(DB_DRIVER, logger)


def test_save_soa_snapshots_of_locked_and_released_study_versions(migration):
    """Each LOCKED or RELEASED study version has exactly one Protocol SoA snapshot and one Protocol Lab table SoA
    snapshot, with all renderings, and no other study version has a SoA snapshot.

    That every legacy SoA snapshot was converted is verified by test_remove_legacy_protocol_soa_cell_relationships,
    as legacy relationships are only removed from study versions that have a Protocol SoA snapshot.
    """
    logger.info("Verify SoA snapshots of LOCKED and RELEASED study versions")

    for layout in ("protocol", "protocol_lab_table"):
        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot)-[has_version:HAS_VERSION {status: 'RELEASED'}]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value, collect(has_version.version) AS versions
            OPTIONAL MATCH (study_value)-[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot {layout: $layout})
            WITH study_root, versions, collect(snapshot) AS snapshots
            WHERE size(snapshots) <> 1
                OR any(snapshot IN snapshots WHERE snapshot.html IS NULL OR snapshot.docx IS NULL
                    OR snapshot.xlsx IS NULL OR snapshot.json IS NULL OR snapshot.time_unit IS NULL)
            RETURN study_root.uid AS study_uid, versions, size(snapshots) AS snapshot_count
            """,
            {"layout": layout},
        )
        assert (
            not records
        ), f"Study versions with missing, duplicate or incomplete {layout} SoA snapshots: {[record.data() for record in records]}"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_value:StudyValue)-[:HAS_SOA_SNAPSHOT]->(:StudySoASnapshot)
        WHERE NOT (:StudyRoot)-[:HAS_VERSION {status: 'RELEASED'}]->(study_value)
        RETURN count(DISTINCT study_value) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "Only LOCKED or RELEASED study versions may have a SoA snapshot"


def test_soa_snapshots_are_returned_by_flowchart_endpoints(migration):
    """The flowchart endpoints return the saved SoA snapshot of each LOCKED or RELEASED study version, of any study,
    for both layouts, as it is."""
    logger.info("Verify flowchart endpoints return the saved SoA snapshots")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[has_version:HAS_VERSION {status: 'RELEASED'}]->(study_value:StudyValue)
            -[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot)
        WITH study_root.uid AS study_uid, study_value, snapshot,
            head(collect(has_version.version)) AS version
        RETURN study_uid, version, snapshot.layout AS layout, snapshot.html AS html, snapshot.json AS json
        ORDER BY study_uid, version, layout
        """,
    )
    assert records, "No SoA snapshots found"

    for record in records:
        study_uid, version, layout = (
            record["study_uid"],
            record["version"],
            record["layout"],
        )
        params = {"study_value_version": version, "layout": layout}
        description = f"{layout} SoA of study {study_uid} version {version}"
        assert (
            api_get(f"/studies/{study_uid}/flowchart.html", params=params).text
            == record["html"]
        ), f"HTML of {description} is not the saved snapshot"
        assert api_get(
            f"/studies/{study_uid}/flowchart", params=params
        ).json() == _without_none(
            json.loads(record["json"])
        ), f"JSON of {description} is not the saved snapshot"


def test_protocol_soa_snapshot_rendered_from_legacy_snapshot(migration):
    """Uses fixture-specific data — not reused by verification_024.

    The test data has a legacy SoA snapshot that is missing a checkmark which the study selections have,
    so the saved Protocol SoA snapshot of that study version differs from the SoA built from its selections.
    """
    logger.info("Verify Protocol SoA snapshot is rendered from the legacy SoA snapshot")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[has_version:HAS_VERSION {status: 'RELEASED'}]->(study_value:StudyValue)
            -[:HAS_SOA_SNAPSHOT]->(:StudySoASnapshot {layout: 'protocol'})
        WITH study_root.uid AS study_uid, study_value, head(collect(has_version.version)) AS version
        RETURN study_uid, version
        ORDER BY study_uid, version
        """,
    )

    differing_snapshots = []
    for record in records:
        study_uid, version = record["study_uid"], record["version"]
        params = {"study_value_version": version, "layout": "protocol"}
        soa = api_get(f"/studies/{study_uid}/flowchart", params=params).json()
        built_soa = api_get(
            f"/studies/{study_uid}/flowchart", params=params | {"force_build": True}
        ).json()
        if _count_checkmarks(soa) != _count_checkmarks(built_soa):
            differing_snapshots.append(
                (
                    study_uid,
                    version,
                    _count_checkmarks(soa),
                    _count_checkmarks(built_soa),
                )
            )

    assert differing_snapshots, (
        "No Protocol SoA snapshot differs from the SoA built from the study selections,"
        " the legacy SoA snapshots were not used"
    )
    assert all(
        saved == built - 1 for _, _, saved, built in differing_snapshots
    ), f"Unexpected checkmark counts (study, version, saved, built): {differing_snapshots}"


def _without_none(value):
    """Removes None values from nested dicts, like the API with response_model_exclude_none"""
    if isinstance(value, dict):
        return {k: _without_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_without_none(v) for v in value]
    return value


def _count_checkmarks(soa: dict) -> int:
    return sum(
        cell.get("text") == "X"
        for row in soa["rows"][soa["num_header_rows"] :]
        for cell in row["cells"]
    )


@pytest.mark.order(
    after="test_save_soa_snapshots_of_locked_and_released_study_versions"
)
def test_repeat_save_soa_snapshots_of_locked_and_released_study_versions(
    migration,
):
    assert not migration_024.save_soa_snapshots_of_locked_and_released_study_versions(
        DB_DRIVER, logger
    )


def test_remove_legacy_protocol_soa_cell_relationships(migration):
    """No legacy SoA snapshot relationships remain."""
    logger.info("Verify legacy SoA snapshot relationships are removed")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH ()-[legacy:HAS_PROTOCOL_SOA_CELL|HAS_PROTOCOL_SOA_FOOTNOTE]->()
        RETURN count(legacy) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "HAS_PROTOCOL_SOA_CELL and HAS_PROTOCOL_SOA_FOOTNOTE relationships must be removed"


@pytest.mark.order(after="test_remove_legacy_protocol_soa_cell_relationships")
def test_repeat_remove_legacy_protocol_soa_cell_relationships(migration):
    assert not migration_024.remove_legacy_protocol_soa_cell_relationships(
        DB_DRIVER, logger
    )
