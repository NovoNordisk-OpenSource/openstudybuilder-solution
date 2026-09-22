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


# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=broad-except

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

# pylint: disable=invalid-name
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
    """STRESC codelists must be flagged is_ordinal, and their terms' HAS_TERM.ordinal
    must reflect the term's submission_value when it's an integer, or be unset otherwise.
    """
    logger.info("Verifying set_ordinal_for_stresc_codelists results")

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


@pytest.mark.order(after="test_set_ordinal_for_stresc_codelists")
def test_non_stresc_codelists_not_marked_ordinal(migration):
    """Codelists without STRESC in their name must not have been flagged ordinal, nor have
    ordinal set on their HAS_TERM relationships, by this migration."""
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


@pytest.mark.order(after="test_non_stresc_codelists_not_marked_ordinal")
def test_stresc_codelist_without_integer_terms_not_marked_ordinal(migration):
    """A codelist whose name contains STRESC but none of whose terms have an integer-like
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

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue)
        MATCH (root)-[:LATEST_FINAL]->(value)
        MATCH (root)-[hv:HAS_VERSION]->(value)
        WHERE hv.end_date IS NULL AND hv.status = 'Final' AND hv.version = '1.0'
        RETURN count(root) AS count
        """,
    )
    assert (
        records[0]["count"] == 2
    ), "Expected exactly two migrated FeatureFlagRoot nodes"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue {name: 'demo_flag'})
        MATCH (root)-[:LATEST_FINAL]->(value)
        MATCH (root)-[hv:HAS_VERSION]->(value)
        WHERE hv.end_date IS NULL
        RETURN
          value.section AS section,
          value.feature AS feature,
          value.enabled AS enabled,
          value.description AS description,
          root.uid AS uid,
          root.legacy_sn AS legacy_sn,
          hv.status AS status,
          hv.version AS version
        """,
    )
    assert records, "demo_flag must exist as FeatureFlagValue"
    assert records[0]["section"] == "admin"
    assert records[0]["feature"] == "Demo Feature"
    assert records[0]["enabled"] is True
    assert records[0]["description"] == "Demo description"
    assert records[0]["uid"].startswith("FeatureFlag_")
    assert records[0]["legacy_sn"] == 1
    assert records[0]["status"] == "Final"
    assert records[0]["version"] == "1.0"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue {name: 'studies_flag'})
        RETURN
          value.section AS section,
          value.feature AS feature,
          value.enabled AS enabled,
          value.description AS description,
          root.legacy_sn AS legacy_sn
        """,
    )
    assert records, "studies_flag must exist as FeatureFlagValue"
    assert records[0]["section"] == "studies"
    assert records[0]["feature"] == "Studies Feature"
    assert records[0]["enabled"] is False
    assert records[0]["description"] is None
    assert records[0]["legacy_sn"] == 2


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
        RETURN count(oiv) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "No OdmItemValue nodes should have the datatype string property after migration"


def test_odm_item_has_data_type_relationships(migration):
    """
    OdmItemValue nodes that had a datatype should now have a HAS_DATA_TYPE
    relationship pointing to the correct CTTermRoot via a CTTermContext node.
    """
    logger.info("Verifying all OdmItemValue nodes have HAS_DATA_TYPE relationships")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (oiv:OdmItemValue)
        WHERE NOT EXISTS {(oiv)-[:HAS_DATA_TYPE]->()}
        RETURN count(oiv) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "All OdmItemValue must have HAS_DATA_TYPE pointing to CTTermContext"


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
        MATCH (u:UnitDefinitionValue)
        RETURN COUNT(u) AS count
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
    """Uses fixture-specific data — not reused by verification_025."""
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