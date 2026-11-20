"""Schema migrations needed to release 2.10 & 2.11 in PROD"""

import json
import os

import httpx
from import_sponsor_data.importers.utils.sponsor_model_schema import SponsorModelSchema

from migrations.common import migrate_indexes_and_constraints
from migrations.utils.utils import (
    SchemaMigrationNode,
    api_get,
    api_post,
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-2.10"

SPONSOR_LIBRARY_NAME = "Sponsor"

# Rendering HTML, DOCX, XLSX and JSON of the Protocol SoA of a large study takes longer than the default timeout
SOA_SNAPSHOT_TIMEOUT_SECONDS = 600
SOA_SNAPSHOT_LAYOUTS = ("protocol", "protocol_lab_table")

# Map study field data types (taken from CTConfigValue.study_field_data_type)
# to the submission_value of the matching CTTerm in the SEMTCDT codelist
# (Semantic Data Type).
STUDY_FIELD_DATA_TYPE_TO_SEMANTIC_DATA_TYPE = {
    "text": "text",
    "registry": "text",
    "project": "text",
    "int": "integer",
    "bool": "boolean",
    "date": "datetime",
    "time": "durationDatetime",
    "multiselect": "ctTerm",
}

# Map CTConfigValue.study_field_grouping to the page_reference set on the
# corresponding MetaStudyField node.
STUDY_FIELD_GROUPING_TO_PAGE_REFERENCE = {
    "study_population": "/population",
    "study_intervention": "/study_properties/attributes",
    "high_level_study_design": "/study_properties/type",
    "id_metadata.registry_identifiers": "/registry_identifiers",
}
# Root of the sponsor model source data (relative to db_schema_migration/, the
# cwd migrations are run from). Each subfolder with a model_info.json is one
# sponsor model; 'schemas' has none and is skipped.
SPONSOR_MODEL_DATAFILES_DIR = os.path.join(
    "..", "import_sponsor_data", "datafiles", "sponsor_library", "sponsormodel"
)

# Submission value of the DATATYPE codelist in
# DDF CT (matches settings.ddf_odm_data_type_cl_submval)
DATATYPE_CODELIST_SUBMVAL = "CODMDT"

# Submission value of the Semantic Data Type codelist that MetaStudyField
# nodes are linked to
SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL = "SEMTCDT"

# Every SEMTCDT term migrate_meta_study_fields may link to: the mapped data
# types plus 'ctTerm', used for text fields that point to a CT term
REQUIRED_SEMANTIC_DATA_TYPE_SUBMVALS = frozenset(
    STUDY_FIELD_DATA_TYPE_TO_SEMANTIC_DATA_TYPE.values()
) | {"ctTerm"}

# Both codelists are sponsor codelists loaded by the import_sponsor_data
# 'codelistterms2' step (sponsor_codelist_definitions.csv, datatype.csv)
DATATYPE_CODELISTS_IMPORT_HINT = (
    "load them first with the import_sponsor_data 'codelistterms2' step"
    " (sponsor_codelist_definitions.csv and datatype.csv)"
)

# Control Type study field changes from single-select (StudyTextField) to
# multi-select (StudyArrayField); the field name follows the plural `_codes`
# convention used by every other multi-select study field.
CONTROL_TYPE_OLD_FIELD_NAME = "control_type_code"
CONTROL_TYPE_NEW_FIELD_NAME = "control_type_codes"


def uppercase_project_numbers(db_driver, log) -> bool:
    """Uppercasing project_number property for all Project nodes where it's not null or already uppercased."""

    log.info("Uppercasing Project.project_number")
    records, summary = run_cypher_query(
        db_driver,
        """
        MATCH (p:Project) WHERE p.project_number IS NOT NULL and p.project_number <> toUpper(p.project_number)
        SET p.project_number = toUpper(p.project_number)
        RETURN p
        """,
    )
    for record in records:
        project = record["p"]
        log.info(
            "Project '%s' [%s]: %s",
            project["name"],
            project["uid"],
            project["project_number"],
        )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def change_catalogue_of_datatype_codelist(db_driver, log) -> bool:
    """
    Changing catalogue of Datatype codelist from 'SDTM CT' to 'DDF CT'.
    """

    log.info("Changing catalogue of DATATYPE codelist from 'SDTM CT' to 'DDF CT'")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (cc:CTCatalogue)-[hc:HAS_CODELIST]->(ccr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
        (:CTCodelistAttributesRoot)-[:LATEST]->(cca:CTCodelistAttributesValue)
        WHERE cc.name = "SDTM CT" AND cca.submission_value = "DATATYPE"
        DELETE hc
        WITH ccr
        MATCH (new_cc:CTCatalogue {name: "DDF CT"})
        CREATE (new_cc)-[:HAS_CODELIST]->(ccr)
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def move_codelist_properties_to_name_value(db_driver, log) -> bool:
    """Move is_ordinal and codelist_type from CTCodelistAttributesValue to CTCodelistNameValue.

    For each CTCodelistRoot, copy the properties from the LATEST
    CTCodelistAttributesValue to all linked CTCodelistNameValue nodes,
    then remove them from all CTCodelistAttributesValue nodes.
    """

    # Step 1: Copy properties from the latest attributes value to all name values.
    log.info(
        "Copying is_ordinal and codelist_type from LATEST CTCodelistAttributesValue "
        "to all CTCodelistNameValue versions"
    )
    _, summary_copy = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(av:CTCodelistAttributesValue)
        WHERE av.is_ordinal IS NOT NULL OR av.codelist_type IS NOT NULL
        MATCH (clr)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[]->(nv:CTCodelistNameValue)
        SET nv.is_ordinal = coalesce(av.is_ordinal, false),
            nv.codelist_type = coalesce(av.codelist_type, 'Standard')
        """,
    )
    print_counters_table(summary_copy.counters)

    # Step 2: Set defaults on any CTCodelistNameValue nodes not covered by step 1.
    log.info("Setting defaults on remaining CTCodelistNameValue nodes")
    _, summary_defaults = run_cypher_query(
        db_driver,
        """
        MATCH (nv:CTCodelistNameValue)
        WHERE nv.is_ordinal IS NULL OR nv.codelist_type IS NULL
        SET nv.is_ordinal = coalesce(nv.is_ordinal, false),
            nv.codelist_type = coalesce(nv.codelist_type, 'Standard')
        """,
    )
    print_counters_table(summary_defaults.counters)

    # Step 3: Remove properties from all CTCodelistAttributesValue nodes.
    log.info("Removing is_ordinal and codelist_type from CTCodelistAttributesValue")
    _, summary_remove = run_cypher_query(
        db_driver,
        """
        MATCH (av:CTCodelistAttributesValue)
        WHERE av.is_ordinal IS NOT NULL OR av.codelist_type IS NOT NULL
        REMOVE av.is_ordinal, av.codelist_type
        """,
    )
    print_counters_table(summary_remove.counters)

    return (
        summary_copy.counters.contains_updates
        or summary_defaults.counters.contains_updates
        or summary_remove.counters.contains_updates
    )


def ensure_archived_library(log) -> bool:
    """Create the Archived library via the API if it is missing (idempotent)."""
    log.info("Ensuring Archived library exists (POST /libraries)")
    libs = api_get("/libraries").json()
    if any(lib.get("name") == "Archived" for lib in libs):
        return False
    api_post("/libraries", {"name": "Archived", "is_editable": False})
    return True


def migrate_feature_flags_to_root_value(db_driver, log) -> bool:
    """
    Create FeatureFlagRoot/Value from flat :FeatureFlag, assess parity, then delete flats.
    """
    log.info("Migrating flat FeatureFlag nodes to FeatureFlagRoot/FeatureFlagValue")

    old_flags, _ = run_cypher_query(
        db_driver,
        """
        MATCH (old:FeatureFlag)
        RETURN count(old) AS old_count
        """,
    )
    old_count = old_flags[0]["old_count"] if old_flags else 0
    if old_count == 0:
        log.info("No flat FeatureFlag nodes found; migration already complete")
        return False

    # Abort only on true orphan roots. This still allows rerun after partial failure,
    # where old :FeatureFlag nodes and migrated roots temporarily coexist.
    orphan_roots, _ = run_cypher_query(
        db_driver,
        """
        MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue)
        WHERE NOT EXISTS {
          MATCH (:FeatureFlag {name: value.name})
        }
        RETURN count(root) AS orphan_roots
        """,
    )
    orphan_root_count = orphan_roots[0]["orphan_roots"] if orphan_roots else 0
    if orphan_root_count:
        raise RuntimeError(
            f"Cannot migrate: found {orphan_root_count} orphan FeatureFlagRoot node(s)"
        )

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (old:FeatureFlag)
        WHERE NOT EXISTS {
          MATCH (:FeatureFlagRoot)-[:LATEST]->(:FeatureFlagValue {name: old.name})
        }
        CALL {
          WITH old
          MERGE (counter:Counter {counterId: 'FeatureFlagCounter'})
          ON CREATE SET counter:FeatureFlagCounter, counter.count = 0
          WITH old, counter
          CALL apoc.lock.nodes([counter])
          SET counter.count = counter.count + 1
          WITH old, counter.count AS uid_number
          CREATE (root:FeatureFlagRoot)
          SET root.uid = 'FeatureFlag_' + apoc.text.lpad('' + uid_number, 6, '0'),
              root.legacy_sn = old.sn
          CREATE (value:FeatureFlagValue)
          SET
            value.section = old.section,
            value.feature = old.feature,
            value.name = old.name,
            value.enabled = old.enabled,
            value.description = old.description
          CREATE (root)-[:LATEST]->(value)
          CREATE (root)-[:LATEST_FINAL]->(value)
          CREATE (root)-[:HAS_VERSION {
            version: '1.0',
            status: 'Final',
            start_date: datetime(),
            end_date: null,
            author_id: 'schema-migration',
            change_description: 'Migrated from flat FeatureFlag'
          }]->(value)
          RETURN root
        }
        RETURN count(*) AS migrated
        """,
    )
    print_counters_table(summary.counters)

    fails, _ = run_cypher_query(
        db_driver,
        """
        MATCH (old:FeatureFlag)
        OPTIONAL MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue {name: old.name})
        OPTIONAL MATCH (root)-[hv:HAS_VERSION]->(value) WHERE hv.end_date IS NULL
        OPTIONAL MATCH (root)-[:LATEST_FINAL]->(lf:FeatureFlagValue)
        WITH old, root, value, hv, lf
        WHERE root IS NULL
           OR value IS NULL
           OR hv IS NULL
           OR lf IS NULL
           OR elementId(lf) <> elementId(value)
           OR coalesce(value.section, '') <> coalesce(old.section, '')
           OR coalesce(value.feature, '') <> coalesce(old.feature, '')
           OR coalesce(value.name, '') <> coalesce(old.name, '')
           OR coalesce(value.enabled, false) <> coalesce(old.enabled, false)
           OR coalesce(value.description, '') <> coalesce(old.description, '')
        RETURN count(*) AS fails
        """,
    )
    fail_count = fails[0]["fails"] if fails else 0
    if fail_count:
        raise RuntimeError(
            f"Account assessment failed with {fail_count} mismatches; "
            "old FeatureFlag nodes were NOT deleted"
        )

    log.info("Account assessment passed; deleting flat FeatureFlag nodes")
    _, delete_summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:FeatureFlag)
        DETACH DELETE n
        """,
    )
    print_counters_table(delete_summary.counters)

    remaining, _ = run_cypher_query(
        db_driver,
        """
        MATCH (n:FeatureFlag)
        RETURN count(n) AS remaining
        """,
    )
    if remaining and remaining[0]["remaining"] != 0:
        raise RuntimeError("Flat FeatureFlag nodes still present after delete")

    return summary.counters.contains_updates or delete_summary.counters.contains_updates


def link_sponsor_model_values_to_library(db_driver, log) -> bool:
    """
    Connect every :SponsorModelValue node to the 'Sponsor' :Library via
    CONTAINS_SPONSOR_MODEL.

    Previously, a sponsor model's library was implicitly the library of the
    (shared) Implementation Guide root it extends (e.g. SDTMIG -> CDISC),
    which is incorrect since a sponsor model is always sponsor-owned content.
    Each SponsorModelValue now tracks its own library explicitly.
    """
    log.info(
        "Linking SponsorModelValue nodes without a Library to '%s'",
        SPONSOR_LIBRARY_NAME,
    )

    missing, _ = run_cypher_query(
        db_driver,
        """
        MATCH (value:SponsorModelValue)
        WHERE NOT EXISTS { MATCH (:Library)-[:CONTAINS_SPONSOR_MODEL]->(value) }
        RETURN count(value) AS missing_count
        """,
    )
    missing_count = missing[0]["missing_count"] if missing else 0
    if missing_count == 0:
        log.info("All SponsorModelValue nodes already linked to a Library; skipping")
        return False

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (value:SponsorModelValue)
        WHERE NOT EXISTS { MATCH (:Library)-[:CONTAINS_SPONSOR_MODEL]->(value) }
        MATCH (library:Library {name: $library_name})
        MERGE (library)-[:CONTAINS_SPONSOR_MODEL]->(value)
        """,
        {"library_name": SPONSOR_LIBRARY_NAME},
    )
    print_counters_table(summary.counters)

    remaining, _ = run_cypher_query(
        db_driver,
        """
        MATCH (value:SponsorModelValue)
        WHERE NOT EXISTS { MATCH (:Library)-[:CONTAINS_SPONSOR_MODEL]->(value) }
        RETURN count(value) AS remaining
        """,
    )
    remaining_count = remaining[0]["remaining"] if remaining else 0
    if remaining_count:
        raise RuntimeError(
            f"{remaining_count} SponsorModelValue node(s) still not linked to a "
            f"Library after migration; does the '{SPONSOR_LIBRARY_NAME}' Library "
            "exist in the database?"
        )

    return summary.counters.contains_updates


def link_dataset_variable_to_data_model_catalogue(db_driver, log) -> bool:
    """
    Link all "orphan" :DatasetVariable nodes to the 'SDTMIG' :DataModelCatalogue via
    HAS_DATASET_VARIABLE.

    These DMCatalogue-less nodes were created in the past due to an oversight
    in the Dataset creation process, where DatasetInstance would create
    DatasetVariable nodes to serve as their keys, but the relationship
    to the DataModelCatalogue was not created.
    This happened only during the creation of Sponsor Models, so we can safely pick
    'SDTMIG' as the default catalogue for these orphan nodes.
    """
    log.info("Linking DatasetVariable nodes without a DataModelCatalogue to 'SDTMIG'")

    missing, _ = run_cypher_query(
        db_driver,
        """
        MATCH (var:DatasetVariable)
        WHERE NOT EXISTS { MATCH (:DataModelCatalogue)-[:HAS_DATASET_VARIABLE]->(var) }
        RETURN count(var) AS missing_count
        """,
    )
    missing_count = missing[0]["missing_count"] if missing else 0
    if missing_count == 0:
        log.info(
            "All DatasetVariable nodes already linked to a DataModelCatalogue; skipping"
        )
        return False

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (var:DatasetVariable)
        WHERE NOT EXISTS { MATCH (:DataModelCatalogue)-[:HAS_DATASET_VARIABLE]->(var) }
        MATCH (catalogue:DataModelCatalogue {name: 'SDTMIG'})
        MERGE (catalogue)-[:HAS_DATASET_VARIABLE]->(var)
        """,
    )
    print_counters_table(summary.counters)

    remaining, _ = run_cypher_query(
        db_driver,
        """
        MATCH (var:DatasetVariable)
        WHERE NOT EXISTS { MATCH (:DataModelCatalogue)-[:HAS_DATASET_VARIABLE]->(var) }
        RETURN count(var) AS remaining
        """,
    )
    remaining_count = remaining[0]["remaining"] if remaining else 0
    if remaining_count:
        raise RuntimeError(
            f"{remaining_count} DatasetVariable node(s) still not linked to a "
            f"DataModelCatalogue after migration; does the 'SDTMIG' DataModelCatalogue "
            "exist in the database?"
        )

    return summary.counters.contains_updates


def _get_codelist_term_submission_values(db_driver, codelist_submval: str) -> set:
    """Submission values of the terms of the codelist with the given submission value."""
    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (:CTCodelistAttributesValue {submission_value: $codelist_submval})
              <-[:LATEST]-(:CTCodelistAttributesRoot)
              <-[:HAS_ATTRIBUTES_ROOT]-(:CTCodelistRoot)
              -[:HAS_TERM]->(clt:CTCodelistTerm)
              -[:HAS_TERM_ROOT]->(:CTTermRoot)
        RETURN collect(DISTINCT clt.submission_value) AS submission_values
        """,
        params={"codelist_submval": codelist_submval},
    )
    return set(records[0]["submission_values"]) if records else set()


def check_datatype_codelists(db_driver, log) -> None:
    """Fail before any data is changed when a data type codelist the migration needs is missing.

    - `migrate_meta_study_fields` links MetaStudyField nodes to SEMTCDT terms. Without them
      no MetaStudyField is created, and `remove_ct_config_nodes` then deletes the CTConfig
      nodes it reads from, so the step cannot be repeated.
    - `migrate_odm_item_datatype_to_ct_term` links OdmItemValue nodes to CODMDT terms.

    Each codelist is only required while there is still data to migrate with it, so a repeated
    run on an already migrated database passes.
    """
    log.info(
        "Checking that the %s and %s codelists are present",
        SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL,
        DATATYPE_CODELIST_SUBMVAL,
    )
    records, _ = run_cypher_query(
        db_driver,
        """
        RETURN
            EXISTS {
                MATCH (cv:CTConfigValue)
                WHERE cv.study_field_name IS NOT NULL
                  AND NOT cv.study_field_name ENDS WITH '_null_value_code'
            } AS has_study_fields,
            EXISTS {
                MATCH (oiv:OdmItemValue)
                WHERE oiv.datatype IS NOT NULL
                  AND toLower(oiv.datatype) <> 'comment'
                  AND NOT (oiv)-[:HAS_DATA_TYPE]->(:CTTermContext)
            } AS has_odm_item_datatypes
        """,
    )
    has_study_fields = records[0]["has_study_fields"]
    has_odm_item_datatypes = records[0]["has_odm_item_datatypes"]
    problems = []

    if has_study_fields:
        missing = REQUIRED_SEMANTIC_DATA_TYPE_SUBMVALS - (
            _get_codelist_term_submission_values(
                db_driver, SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL
            )
        )
        if missing:
            problems.append(
                f"{SEMANTIC_DATA_TYPE_CODELIST_SUBMVAL} codelist is missing terms"
                f" {sorted(missing)}, needed to create MetaStudyField nodes from the"
                " CTConfigValue nodes"
            )

    if has_odm_item_datatypes and not _get_codelist_term_submission_values(
        db_driver, DATATYPE_CODELIST_SUBMVAL
    ):
        problems.append(
            f"{DATATYPE_CODELIST_SUBMVAL} codelist (or all of its terms) is missing,"
            " needed to link OdmItemValue nodes to their data type"
        )

    if problems:
        raise RuntimeError(
            "Migration prerequisites not met, no data was changed: "
            + "; ".join(problems)
            + f"; {DATATYPE_CODELISTS_IMPORT_HINT}"
        )


def migrate_meta_study_fields(db_driver, log) -> bool:
    """Pre-create MetaStudyField nodes and link them to the matching
    Semantic Data Type CTTermRoot (SEMTCDT codelist).

    Source of truth is the existing `CTConfigValue` nodes (which carry
    `study_field_name` and `study_field_data_type`). This function MUST run
    BEFORE `remove_ct_config_nodes`, otherwise there will be nothing left to
    read from.

    For every `CTConfigValue` whose `study_field_name` does NOT end with
    `_null_value_code`, the resulting graph shape is:

        (MetaStudyField {osb_field_name: <study_field_name>,
                         osb_page_reference: <page_reference>})
            -[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
            -[:HAS_SELECTED_TERM]->(:CTTermRoot)   // SEMTCDT term

    The SEMTCDT CTTermRoot is resolved by matching the
    `CTCodelistTerm.submission_value` (on the `HAS_TERM` link from the
    codelist) against the value derived from `study_field_data_type` via
    STUDY_FIELD_DATA_TYPE_TO_SEMANTIC_DATA_TYPE.
    """
    log.info(
        "Pre-creating MetaStudyField nodes with HAS_SEMANTIC_DATA_TYPE links"
        " from existing CTConfigValue nodes"
    )

    config_rows, _ = run_cypher_query(
        db_driver,
        """
        MATCH (cv:CTConfigValue)
        WHERE cv.study_field_name IS NOT NULL
          AND NOT cv.study_field_name ENDS WITH '_null_value_code'
        RETURN DISTINCT
            cv.study_field_name AS field_name,
            cv.study_field_data_type AS data_type,
            cv.study_field_grouping AS grouping,
            EXISTS {
                (sf:StudyField {field_name: cv.study_field_name})
                    -[:HAS_TYPE]->(:CTTermContext)
            } AS has_ct_type
        """,
    )

    contains_updates = False
    skipped_data_types: set[str] = set()
    missing_semtcdt_terms: set[str] = set()

    for row in config_rows:
        field_name = row["field_name"]
        data_type = row["data_type"]
        grouping = row["grouping"]
        has_ct_type = row["has_ct_type"]
        page_reference = STUDY_FIELD_GROUPING_TO_PAGE_REFERENCE.get(grouping)

        sdt_submission_value = STUDY_FIELD_DATA_TYPE_TO_SEMANTIC_DATA_TYPE.get(
            data_type
        )
        if sdt_submission_value is None:
            skipped_data_types.add(str(data_type))
            log.warning(
                "No semantic data type mapping for study_field_data_type='%s'"
                " (study_field_name='%s'), skipping",
                data_type,
                field_name,
            )
            continue

        # Override: text-typed StudyFields that point to a CTTermContext via
        # HAS_TYPE are semantically CTTerm references.
        if sdt_submission_value == "text" and has_ct_type:
            log.info(
                "MetaStudyField '%s' is text-typed but has StudyField"
                " -[:HAS_TYPE]->(:CTTermContext); using semantic type 'ctTerm'",
                field_name,
            )
            sdt_submission_value = "ctTerm"

        records, summary = run_cypher_query(
            db_driver,
            """
            MATCH (:CTCodelistAttributesValue {submission_value: "SEMTCDT"})
                  <-[:LATEST]-(:CTCodelistAttributesRoot)
                  <-[:HAS_ATTRIBUTES_ROOT]-(:CTCodelistRoot)
                  -[:HAS_TERM]->(:CTCodelistTerm {submission_value: $sdt_sv})
                  -[:HAS_TERM_ROOT]->(sdt_root:CTTermRoot)
            WITH sdt_root LIMIT 1
            MERGE (msf:MetaStudyField {osb_field_name: $field_name})
            FOREACH (_ IN CASE WHEN $page_reference IS NULL THEN [] ELSE [1] END |
                SET msf.osb_page_reference = $page_reference
            )
            WITH msf, sdt_root
            WHERE NOT EXISTS {
                (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
                      -[:HAS_SELECTED_TERM]->(:CTTermRoot)
            }
            CREATE (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
                   -[:HAS_SELECTED_TERM]->(sdt_root)
            RETURN sdt_root.uid AS sdt_uid
            """,
            params={
                "field_name": field_name,
                "sdt_sv": sdt_submission_value,
                "page_reference": page_reference,
            },
        )

        if summary.counters.contains_updates:
            contains_updates = True

        if not records:
            probe, _ = run_cypher_query(
                db_driver,
                """
                MATCH (:CTCodelistAttributesValue {submission_value: "SEMTCDT"})
                      <-[:LATEST]-(:CTCodelistAttributesRoot)
                      <-[:HAS_ATTRIBUTES_ROOT]-(:CTCodelistRoot)
                      -[:HAS_TERM]->(:CTCodelistTerm {submission_value: $sdt_sv})
                      -[:HAS_TERM_ROOT]->(:CTTermRoot)
                RETURN count(*) AS c
                """,
                params={"sdt_sv": sdt_submission_value},
            )
            if probe and probe[0]["c"] == 0:
                missing_semtcdt_terms.add(sdt_submission_value)
                log.warning(
                    "No SEMTCDT CTTermRoot found with submission_value='%s'"
                    " for MetaStudyField '%s'",
                    sdt_submission_value,
                    field_name,
                )
            else:
                log.info(
                    "MetaStudyField '%s' already linked to a semantic data type,"
                    " skipping",
                    field_name,
                )
        else:
            log.info(
                "MetaStudyField '%s' linked to SEMTCDT term [%s] (sv='%s')",
                field_name,
                records[0]["sdt_uid"],
                sdt_submission_value,
            )

    if skipped_data_types:
        log.warning(
            "Unmapped study_field_data_type values encountered: %s",
            sorted(skipped_data_types),
        )
    if missing_semtcdt_terms:
        # Fail here, before remove_ct_config_nodes deletes the CTConfigValue nodes read above
        raise RuntimeError(
            f"SEMTCDT submission_values not found in DB: {sorted(missing_semtcdt_terms)};"
            f" {DATATYPE_CODELISTS_IMPORT_HINT}"
        )

    return contains_updates


def migrate_control_type_to_array_field(db_driver, log) -> bool:
    """Convert the Control Type study field from single-select to multi-select.

    Every `StudyTextField {field_name: 'control_type_code'}` node is converted
    in place into a `StudyArrayField {field_name: 'control_type_codes'}`:
    - `value` becomes a list holding the selected CT term uid(s), taken from the
      `HAS_TYPE` term when present, or `[]` when the field only carries a null
      flavor.
    - incoming `HAS_TEXT_FIELD` relationships from `StudyValue` nodes are
      replaced with `HAS_ARRAY_FIELD`.
    Converting in place keeps the `HAS_TYPE`, `HAS_REASON_FOR_NULL_VALUE` and
    audit trail `BEFORE`/`AFTER` relationships attached, so study history is
    preserved.

    The matching `MetaStudyField.osb_field_name` is renamed as well, and the
    linked Trial Summary parameter (TCNTRL) cardinality is set to 'Many'.

    Must run AFTER `migrate_meta_study_fields`, which resolves the semantic data
    type of `control_type_code` from the not-yet-converted StudyTextField nodes.
    """
    log.info(
        "Converting '%s' StudyTextField nodes to '%s' StudyArrayField nodes",
        CONTROL_TYPE_OLD_FIELD_NAME,
        CONTROL_TYPE_NEW_FIELD_NAME,
    )
    params = {
        "old_field_name": CONTROL_TYPE_OLD_FIELD_NAME,
        "new_field_name": CONTROL_TYPE_NEW_FIELD_NAME,
    }

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (sf:StudyTextField {field_name: $old_field_name})
        OPTIONAL MATCH (sf)-[:HAS_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(term:CTTermRoot)
        WITH sf, collect(DISTINCT term.uid) AS term_uids
        REMOVE sf:StudyTextField
        SET sf:StudyArrayField,
            sf.field_name = $new_field_name,
            sf.value = CASE
                WHEN size(term_uids) > 0 THEN term_uids
                WHEN sf.value IS NULL OR sf.value = '' THEN []
                ELSE [sf.value]
            END
        """,
        params,
    )
    print_counters_table(summary_nodes.counters)

    log.info("Replacing HAS_TEXT_FIELD with HAS_ARRAY_FIELD for converted nodes")
    _, summary_rels = run_cypher_query(
        db_driver,
        """
        MATCH (sv:StudyValue)-[old:HAS_TEXT_FIELD]->(sf:StudyArrayField {field_name: $new_field_name})
        MERGE (sv)-[new:HAS_ARRAY_FIELD]->(sf)
        SET new += properties(old)
        DELETE old
        """,
        params,
    )
    print_counters_table(summary_rels.counters)

    log.info("Renaming MetaStudyField '%s'", CONTROL_TYPE_OLD_FIELD_NAME)
    _, summary_msf = run_cypher_query(
        db_driver,
        """
        MATCH (msf:MetaStudyField {osb_field_name: $old_field_name})
        SET msf.osb_field_name = $new_field_name
        """,
        params,
    )
    print_counters_table(summary_msf.counters)

    log.info("Setting cardinality 'Many' on the Control Type TS parameter")
    _, summary_card = run_cypher_query(
        db_driver,
        """
        MATCH (tsp:CTTermNameValue)-[:RELATED_STUDY_FIELD_SELECTION]->
              (:MetaStudyField {osb_field_name: $new_field_name})
        WHERE tsp.cardinality IS NOT NULL AND tsp.cardinality <> 'Many'
        SET tsp.cardinality = 'Many'
        """,
        params,
    )
    print_counters_table(summary_card.counters)

    return (
        summary_nodes.counters.contains_updates
        or summary_rels.counters.contains_updates
        or summary_msf.counters.contains_updates
        or summary_card.counters.contains_updates
    )


def remove_ct_config_nodes(db_driver, log) -> bool:
    """Remove all CTConfigRoot and CTConfigValue nodes.

    Refuses to delete while a study field that `migrate_meta_study_fields` should have
    pre-created has no MetaStudyField with a semantic data type, since the CTConfigValue
    nodes are the only source for that step.
    """
    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (cv:CTConfigValue)
        WHERE cv.study_field_name IS NOT NULL
          AND NOT cv.study_field_name ENDS WITH '_null_value_code'
          AND cv.study_field_data_type IN $mapped_data_types
          AND NOT EXISTS {
              (:MetaStudyField {osb_field_name: cv.study_field_name})
                  -[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
                  -[:HAS_SELECTED_TERM]->(:CTTermRoot)
          }
        RETURN collect(DISTINCT cv.study_field_name) AS field_names
        """,
        params={"mapped_data_types": list(STUDY_FIELD_DATA_TYPE_TO_SEMANTIC_DATA_TYPE)},
    )
    if records and records[0]["field_names"]:
        raise RuntimeError(
            "Not removing CTConfig nodes, study fields without a MetaStudyField"
            f" semantic data type: {sorted(records[0]['field_names'])}"
        )

    log.info("Removing CTConfigRoot/CTConfigValue nodes from database")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n) WHERE n:CTConfigRoot OR n:CTConfigValue
        DETACH DELETE n
        """,
    )
    print_counters_table(summary.counters)

    return summary.counters.contains_updates


def load_sponsor_model_schemas(log) -> bool:
    """
    Publish every Sponsor Model schema version found under
    import_sponsor_data's schemas folder (e.g. sponsor.v1.yaml, sponsor.v2.yaml)
    via POST /standards/sponsor-models/schema.

    Mirrors SponsorModels.handle_schemas() in
    import_sponsor_data/importers/run_import_sponsormodels.py: the
    SponsorModelSchema loader discovers, parses and validates every schema
    file, keyed by its own declared (library_name, schema_version).

    Unlike handle_schemas(), each (library_name, schema_version) is checked
    against the API first (GET) and only POSTed when missing. The endpoint is
    idempotent on identical re-publish (returns 200, not 201), which would
    otherwise fail api_post()'s assertion that a publish returns 201.
    """
    log.info("Publishing Sponsor Model field-schema versions")

    schema_loader = SponsorModelSchema(parser=None)
    published = False
    existing_versions_by_library: dict[str, set] = {}

    for entry in schema_loader.available_schemas():
        library_name = entry["library_name"]
        schema_version = entry["schema_version"]

        if library_name not in existing_versions_by_library:
            existing = api_get(
                "/standards/sponsor-models/schema",
                params={"library_name": library_name},
            ).json()
            existing_versions_by_library[library_name] = {
                item["schema_version"] for item in existing
            }

        if schema_version in existing_versions_by_library[library_name]:
            log.info(
                "Sponsor Model Schema '%s' version %s already published; skipping",
                library_name,
                schema_version,
            )
            continue

        log.info(
            "Publishing Sponsor Model Schema '%s' version %s",
            library_name,
            schema_version,
        )
        api_post(
            "/standards/sponsor-models/schema",
            {
                "library_name": library_name,
                "schema_version": schema_version,
                "schema": entry["schema"],
            },
        )
        existing_versions_by_library[library_name].add(schema_version)
        published = True

    return published


def link_sponsor_model_values_to_schema(db_driver, log) -> bool:
    """
    Connect every :SponsorModelValue node to the :SponsorModelSchemaValue it
    follows, via FOLLOWS_SCHEMA - the same relationship created by
    SponsorModelRepository._link_schema_version() in the API when a sponsor
    model is created with a schema_version.

    The (library_name, schema_version) each sponsor model follows is read from
    its model_info.json - the same file run_import_sponsormodels.py uses to
    build the sponsor model - keyed by `sponsor_model_name`, which is exactly
    the `name` stored on its SponsorModelValue node.

    Idempotent: nodes that already have a FOLLOWS_SCHEMA link are left
    untouched and skipped. Sponsor models with no matching model_info.json (or
    whose schema hasn't been published) are logged and left unlinked rather
    than failing the migration.
    """
    log.info("Linking SponsorModelValue nodes to their Sponsor Model Schema version")

    changes = []
    for dir_name in sorted(os.listdir(SPONSOR_MODEL_DATAFILES_DIR)):
        model_info_path = os.path.join(
            SPONSOR_MODEL_DATAFILES_DIR, dir_name, "model_info.json"
        )
        # Subfolders without a model_info.json - such as the shared 'schemas'
        # folder - are not sponsor models.
        if not os.path.isfile(model_info_path):
            continue

        with open(model_info_path, encoding="utf-8") as f:
            model_info = json.load(f)

        if model_info.get("exclude"):
            continue

        sponsor_model_name = model_info["sponsor_model_name"]
        library_name = model_info.get("library_name", SPONSOR_LIBRARY_NAME)
        schema_version = model_info.get("schema_version", 1)
        schema_root_uid = f"SponsorModelSchema_{library_name}"

        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (value:SponsorModelValue {name: $sponsor_model_name})
            WHERE NOT EXISTS { MATCH (value)-[:FOLLOWS_SCHEMA]->() }
            MATCH (:SponsorModelSchemaRoot {uid: $schema_root_uid})
                  -[:HAS_SCHEMA_VERSION]->(schema_value:SponsorModelSchemaValue {schema_version: $schema_version})
            MERGE (value)-[:FOLLOWS_SCHEMA]->(schema_value)
            """,
            {
                "sponsor_model_name": sponsor_model_name,
                "schema_root_uid": schema_root_uid,
                "schema_version": schema_version,
            },
        )
        print_counters_table(summary.counters)
        changes.append(summary.counters.contains_updates)

    remaining, _ = run_cypher_query(
        db_driver,
        """
        MATCH (value:SponsorModelValue)
        WHERE NOT EXISTS { MATCH (value)-[:FOLLOWS_SCHEMA]->() }
        RETURN count(value) AS remaining
        """,
    )
    remaining_count = remaining[0]["remaining"] if remaining else 0
    if remaining_count:
        log.warning(
            "%s SponsorModelValue node(s) still have no FOLLOWS_SCHEMA link "
            "(no matching model_info.json, or its schema hasn't been published)",
            remaining_count,
        )

    return any(changes)


def set_ordinal_for_stresc_codelists(db_driver, log) -> bool:
    """
    Mark STRESC codelists as ordinal, and set the ordinal value on their HAS_TERM relationships.

    CDISC codelists whose name contains "STRESC" are the "standardized character result"
    codelists: their terms are often the same integer-like values as the corresponding STRESN
    (standardized numeric result) codelist, encoded as strings, plus a few non-numeric catch-all
    terms such as "UNKNOWN" or "N/A". Some STRESC codelists however only ever have non-numeric
    terms (e.g. i0-i4 scale for Rutgeerts), and must NOT be treated as ordinal.

    A CTCodelistNameValue whose name contains "STRESC" is flagged `is_ordinal = true` only if at
    least one of the codelist's terms has an integer submission_value (or a numeric string, e.g.
    "1"). For every `HAS_TERM` relationship from such an (ordinal) codelist's root, `ordinal` is
    set to the linked CTCodelistTerm's submission_value converted to an integer (as a float, to
    match the `ordinal` FloatProperty), or left unset (null) when the submission_value is not an
    integer (e.g. "UNKNOWN", "N/A").

    Must run AFTER `move_codelist_properties_to_name_value` (is_ordinal must already live on
    CTCodelistNameValue by the time this runs).

    Idempotent: only touches CTCodelistNameValue nodes not already flagged, and only rewrites a
    HAS_TERM.ordinal when the computed value differs from what's already stored.
    """
    log.info(
        "Setting is_ordinal=true on STRESC CTCodelistNameValue nodes with at least one "
        "integer-valued term"
    )
    _, summary_names = run_cypher_query(
        db_driver,
        """
        MATCH (cr:CTCodelistRoot)--(cnr:CTCodelistNameRoot)--(cnv:CTCodelistNameValue)
        WHERE cnv.name CONTAINS "STRESC"
          AND coalesce(cnv.is_ordinal, false) = false
          AND EXISTS {
              MATCH (cr)-[:HAS_TERM]->(ct:CTCodelistTerm)
              WHERE toInteger(ct.submission_value) IS NOT NULL
          }
        SET cnv.is_ordinal = true
        """,
    )
    print_counters_table(summary_names.counters)

    log.info("Setting ordinal on HAS_TERM relationships of ordinal STRESC codelists")
    _, summary_terms = run_cypher_query(
        db_driver,
        """
        MATCH (cr:CTCodelistRoot)--(cnr:CTCodelistNameRoot)--(cnv:CTCodelistNameValue)
        WHERE cnv.name CONTAINS "STRESC" AND cnv.is_ordinal = true
        WITH DISTINCT cr
        MATCH (cr)-[ht:HAS_TERM]->(ct:CTCodelistTerm)
        WITH ht, toFloat(toInteger(ct.submission_value)) AS computed_ordinal
        WHERE ht.ordinal <> computed_ordinal
           OR (ht.ordinal IS NULL AND computed_ordinal IS NOT NULL)
           OR (ht.ordinal IS NOT NULL AND computed_ordinal IS NULL)
        SET ht.ordinal = computed_ordinal
        """,
    )
    print_counters_table(summary_terms.counters)

    return (
        summary_names.counters.contains_updates
        or summary_terms.counters.contains_updates
    )


def collect_suffix_groups(db_driver, log) -> list[dict]:
    """Collect one entry per anchor_uid group from SPECIAL_VISIT nodes.

    Each entry has:
      - study_uid: the study of the visits
      - anchor_uid: the visit this group references
      - ordered_uids: visit uids sorted by visit_number (latest version, deduped by uid)
      - anchor_unit_name: unit of the anchor visit's timepoint (defaults to 'days')

    Visits still marked with _migrating=true are collected too, so that a re-run
    after a failure completes the visits already changed to SINGLE_VISIT.

    Visits without a current node in the latest study version (deleted since a locked or released
    study version or from the draft, or belonging to a deleted study) are collected in one extra group
    without a study_uid: they get the suffix and the 0 days timepoint, but no expected_time_value.
    """
    log.info("Collecting suffix groups from SPECIAL_VISIT nodes")
    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_val:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit)
        WHERE (sv.visit_class = 'SPECIAL_VISIT' OR sv._migrating = true)
          AND NOT (study_val)<-[:BEFORE]-(:Delete)
          AND NOT (sv)<-[:BEFORE]-(:StudyAction)
        WITH study_root.uid AS study_uid,
             sv.uid AS visit_uid,
             sv.visit_sublabel_reference AS anchor_uid,
             min(sv.visit_number) AS visit_number
        ORDER BY visit_number
        WITH study_uid, anchor_uid, collect(visit_uid) AS ordered_uids
        OPTIONAL MATCH (:StudyRoot {uid: study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_VISIT]->(anchor:StudyVisit {uid: anchor_uid})
                       -[:HAS_TIMEPOINT]->(:TimePointRoot)-[:LATEST]->(:TimePointValue)
                       -[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue)
        RETURN study_uid, anchor_uid, ordered_uids, coalesce(udv.name, 'days') AS anchor_unit_name
        """,
    )
    groups = [
        {
            "study_uid": r["study_uid"],
            "anchor_uid": r["anchor_uid"],
            "ordered_uids": r["ordered_uids"],
            "anchor_unit_name": r["anchor_unit_name"],
        }
        for r in records
    ]

    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (sv:StudyVisit)
        WHERE (sv.visit_class = 'SPECIAL_VISIT' OR sv._migrating = true)
          AND NOT sv.uid IN $grouped_uids
        RETURN collect(DISTINCT sv.uid) AS uids
        """,
        {"grouped_uids": [uid for g in groups for uid in g["ordered_uids"]]},
    )
    if records[0]["uids"]:
        log.info(
            "Found %d visits not in the latest study version",
            len(records[0]["uids"]),
        )
        groups.append(
            {
                "study_uid": None,
                "anchor_uid": None,
                "ordered_uids": records[0]["uids"],
                "anchor_unit_name": "days",
            }
        )

    log.info(
        "Found %d suffix groups (%d unique anchors)",
        len(groups),
        len({g["anchor_uid"] for g in groups}),
    )
    return groups


def mark_special_visits(db_driver, log) -> bool:
    """Set _migrating=true on all SPECIAL_VISIT nodes before the class change.

    This marker survives the class flip and lets subsequent steps distinguish
    nodes that were genuinely SPECIAL_VISIT from old SINGLE_VISIT versions of the
    same logical visit that share the same uid but must not be stamped.
    """
    log.info("Marking SPECIAL_VISIT nodes with _migrating=true")
    _, summary = run_cypher_query(
        db_driver,
        "MATCH (sv:StudyVisit {visit_class: 'SPECIAL_VISIT'}) SET sv._migrating = true",
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def migrate_odm_item_datatype_to_ct_term(db_driver, log) -> bool:
    """
    For each OdmItemValue node that still carries the legacy `datatype` string property
    and has no HAS_DATA_TYPE relationship, look up the matching CT term in the CODMDT
    codelist, create (or reuse) a CTTermContext node, and connect the OdmItemValue to it
    via HAS_DATA_TYPE.

    The lookup is case-insensitive so that values stored as e.g. "Text" or "TEXT" are
    matched correctly against CTCodelistTerm.submission_value.

    Nodes/relationships that already have HAS_DATA_TYPE are left untouched.

    Items with datatype "comment" (case-insensitive) get no data type: the legacy
    `datatype` property is removed and no HAS_DATA_TYPE relationship is created.
    Items with datatype "text" (case-insensitive) are changed to "STRING" before the lookup.
    """
    log.info("Removing datatype from OdmItemValue nodes with datatype 'comment'")
    _, comment_summary = run_cypher_query(
        db_driver,
        """
        MATCH (oiv:OdmItemValue)
        WHERE toLower(oiv.datatype) = 'comment'
        REMOVE oiv.datatype
        """,
    )
    print_counters_table(comment_summary.counters)

    log.info("Changing OdmItemValue datatype 'text' to 'STRING'")
    _, text_summary = run_cypher_query(
        db_driver,
        """
        MATCH (oiv:OdmItemValue)
        WHERE toLower(oiv.datatype) = 'text'
        SET oiv.datatype = 'STRING'
        """,
    )
    print_counters_table(text_summary.counters)

    log.info("Migrating OdmItemValue.datatype property to HAS_DATA_TYPE relationship")
    records, summary = run_cypher_query(
        db_driver,
        """
        MATCH (oiv:OdmItemValue)
        WHERE oiv.datatype IS NOT NULL

        // Locate the CODMDT codelist
        MATCH (clr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(clav:CTCodelistAttributesValue)
        WHERE clav.submission_value = $codelist_submval

        // Match the term whose submission value equals the stored datatype string
        MATCH (clr)-[:HAS_TERM]->(clt:CTCodelistTerm)
        WHERE toLower(clt.submission_value) = toLower(oiv.datatype)
        MATCH (clt)-[:HAS_TERM_ROOT]->(ctr:CTTermRoot)

        // Create (or reuse) the CTTermContext and wire up the relationship
        MERGE (clr)<-[:HAS_SELECTED_CODELIST]-(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(ctr)
        MERGE (oiv)-[:HAS_DATA_TYPE]->(ctx)

        RETURN count(oiv) AS migrated
        """,
        params={"codelist_submval": DATATYPE_CODELIST_SUBMVAL},
    )
    migrated = records[0]["migrated"] if records else 0
    log.info(
        "Migrated HAS_DATA_TYPE relationship for %d OdmItemValue node(s)", migrated
    )
    print_counters_table(summary.counters)

    return (
        comment_summary.counters.contains_updates
        or text_summary.counters.contains_updates
        or summary.counters.contains_updates
    )


def change_visit_class_to_single(db_driver, log) -> bool:
    """Change visit_class SPECIAL_VISIT → SINGLE_VISIT for all special visits."""
    log.info("Changing visit_class SPECIAL_VISIT -> SINGLE_VISIT")
    _, summary = run_cypher_query(
        db_driver,
        "MATCH (sv:StudyVisit {visit_class: 'SPECIAL_VISIT'}) SET sv.visit_class = 'SINGLE_VISIT'",
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def remove_odm_item_datatype_string_property(db_driver, log) -> bool:
    """
    Remove the legacy `datatype` string property from OdmItemValue nodes that have
    been migrated to a HAS_DATA_TYPE relationship.

    This must run after migrate_odm_item_datatype_to_ct_term. Nodes without a
    HAS_DATA_TYPE relationship (e.g. no CT term matches their datatype string) keep the
    property, so that the original value is not lost; a warning lists them.
    """
    log.info("Removing legacy `datatype` string property from OdmItemValue nodes")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (oiv:OdmItemValue)-[:HAS_DATA_TYPE]->(:CTTermContext)
        WHERE oiv.datatype IS NOT NULL
        REMOVE oiv.datatype
        """,
    )
    print_counters_table(summary.counters)

    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (oiv:OdmItemValue)
        WHERE oiv.datatype IS NOT NULL
          AND NOT (oiv)-[:HAS_DATA_TYPE]->(:CTTermContext)
        RETURN oiv.datatype AS datatype, count(oiv) AS count
        ORDER BY datatype
        """,
    )
    if records:
        log.warning(
            "Kept `datatype` on OdmItemValue nodes without a HAS_DATA_TYPE relationship "
            "(no matching term in the %s codelist): %s",
            DATATYPE_CODELIST_SUBMVAL,
            {record["datatype"]: record["count"] for record in records},
        )
    return summary.counters.contains_updates


def clear_migrating_marker(db_driver, log) -> None:
    """Remove the temporary _migrating marker from all converted visits."""
    log.info("Removing _migrating marker from converted visits")
    run_cypher_query(
        db_driver,
        "MATCH (sv:StudyVisit) WHERE sv._migrating IS NOT NULL REMOVE sv._migrating",
    )


def _stamp_visit_uid(
    db_driver,
    visit_uid: str,
    timepoint_root_uid: str,
    anchor_study_duration_days: int | None,
    log,
) -> bool:
    """SET visit_suffix and expected_time_value, and attach the global anchor timepoint in one query.

    Filters on _migrating=true so only nodes that were SPECIAL_VISIT at migration time
    are touched — old SINGLE_VISIT versions of the same logical visit are left alone.

    expected_time_value keeps the visit at the timing of its anchor visit, in the unit of the timepoint.
    Early discontinuation visits don't get it, they follow their parent visit.
    """
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (sv:StudyVisit {uid: $uid, _migrating: true})
        MATCH (tp:TimePointRoot {uid: $tp_uid})-[:LATEST]->(:TimePointValue)
              -[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(unit:UnitDefinitionValue)
        SET sv.visit_suffix = right(sv.short_visit_label, 1),
            sv.expected_time_value = CASE
                WHEN $days IS NULL OR EXISTS {
                    MATCH (sv)-[:HAS_VISIT_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)
                          -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(:CTTermNameValue {name: 'Early discontinuation'})
                } THEN sv.expected_time_value
                // conversion factors are to seconds
                ELSE toInteger(round($days * 86400 / unit.conversion_factor_to_master))
            END
        MERGE (sv)-[:HAS_TIMEPOINT]->(tp)
        """,
        {
            "uid": visit_uid,
            "tp_uid": timepoint_root_uid,
            "days": anchor_study_duration_days,
        },
    )
    if summary.counters.contains_updates:
        log.info("uid '%s': visit_suffix extracted from short_visit_label", visit_uid)
    return summary.counters.contains_updates


def fetch_anchor_study_duration_days(group: dict, log) -> int | None:
    """Return the timing of the anchor visit in days, resolved by the API through its time references."""
    response = api_get(
        f"/studies/{group['study_uid']}/study-visits/{group['anchor_uid']}",
        check_ok_status=False,
    )
    days = (
        response.json().get("study_duration_days")
        if response.status_code == 200
        else None
    )
    if days is None:
        log.warning("No timing for anchor visit '%s'", group["anchor_uid"])
    return days


def _stamp_suffix_group(db_driver, group: dict, log) -> int:
    """Stamp visit_suffix + expected_time_value + timepoint for all uids in one group.

    The timepoint is resolved up front by migrate_special_visits_to_single_visit.
    """
    days = fetch_anchor_study_duration_days(group, log) if group["study_uid"] else None
    updated = 0
    for visit_uid in group["ordered_uids"]:
        if _stamp_visit_uid(
            db_driver, visit_uid, group["timepoint_root_uid"], days, log
        ):
            updated += 1
    return updated


def assign_suffixes_and_timepoints(db_driver, suffix_groups: list[dict], log) -> bool:
    """For each anchor group: stamp visit_suffix and HAS_TIMEPOINT on every version node."""
    total = sum(_stamp_suffix_group(db_driver, group, log) for group in suffix_groups)
    log.info("Assigned suffix+timepoint to %d visit uids", total)
    return total > 0


def fetch_global_anchor_timepoint_uid(db_driver, unit_name: str) -> str | None:
    """Return the uid of an existing TimePointRoot for '0 {unit_name} after Global anchor visit'."""
    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (tp_root:TimePointRoot)-[:LATEST]->(tp_val:TimePointValue)
        MATCH (tp_val)-[:HAS_VALUE]->(:NumericValueRoot)-[:LATEST]->(nv:NumericValue)
        WHERE nv.value = 0.0
        MATCH (tp_val)-[:HAS_TIME_REFERENCE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ref_root:CTTermRoot)
        MATCH (ref_root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(ref_name:CTTermNameValue)
        WHERE ref_name.name = 'Global anchor visit'
        MATCH (tp_val)-[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(unit_val:UnitDefinitionValue)
        WHERE unit_val.name = $unit_name
        RETURN tp_root.uid AS uid
        LIMIT 1
        """,
        {"unit_name": unit_name},
    )
    return records[0]["uid"] if records else None


def migrate_special_visits_to_single_visit(db_driver, log) -> bool:
    """Migrate all SPECIAL_VISIT nodes to SINGLE_VISIT.

    Every converted visit receives:
    - visit_suffix (A/B/C… for non-ED, X/Y/Z for ED) per anchor group
    - HAS_TIMEPOINT → 0 <unit> / Global anchor visit (unit matches the anchor visit)
    - expected_time_value set to the timing of the anchor visit (not for Early discontinuation visits)

    The visit type and visit_sublabel_reference (the old anchor visit) of converted visits are left untouched.
    """
    log.info("=== Migrating all SPECIAL_VISIT nodes to SINGLE_VISIT ===")
    had_updates = False

    suffix_groups = collect_suffix_groups(db_driver, log)
    if suffix_groups:
        # Resolve every required timepoint before any write
        for group in suffix_groups:
            group["timepoint_root_uid"] = fetch_global_anchor_timepoint_uid(
                db_driver, group["anchor_unit_name"]
            )
        missing_units = sorted(
            {
                g["anchor_unit_name"]
                for g in suffix_groups
                if not g["timepoint_root_uid"]
            }
        )
        if missing_units:
            raise RuntimeError(
                "Could not find a TimePointRoot for '0 <unit> / Global anchor visit' "
                f"for units {missing_units}; aborting before any SPECIAL_VISIT is changed."
            )

        # Mark before the class change so _migrating=true survives the flip and
        # identifies exactly which version nodes to stamp — old SINGLE_VISIT versions
        # of the same logical visit are not marked and will be left alone.
        # The marker also lets a re-run find the visits once the class has changed.
        mark_special_visits(db_driver, log)

        # Before stamping: the anchor timings are read from the API, which no longer knows SPECIAL_VISIT
        change_visit_class_to_single(db_driver, log)

        had_updates = assign_suffixes_and_timepoints(db_driver, suffix_groups, log)
        clear_migrating_marker(db_driver, log)
    else:
        log.info(
            "No SPECIAL_VISIT nodes found; skipping class change and suffix assignment"
        )

    log.info("=== SPECIAL_VISIT migration complete ===")
    return had_updates


def _get_study_uids_with_visits(db_driver) -> list[str]:
    """Return UIDs of all studies that have at least one current StudyVisit."""
    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (sr:StudyRoot)-[:LATEST]->(study_val:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit)
        WHERE NOT (study_val)<-[:BEFORE]-(:Delete)
          AND NOT (sv)<-[:BEFORE]-(:StudyAction)
        RETURN DISTINCT sr.uid AS study_uid
        """,
    )
    return [r["study_uid"] for r in records]


def _assign_visit_order_for_study(db_driver, study_uid: str, log) -> int | None:
    """Call the API to get the ordered visit list for one study and write its `order` to each node.

    Returns the number of nodes updated, or None if the API call failed.
    """
    response = api_get(
        f"/studies/{study_uid}/study-visits",
        params={"page_size": 0, "total_count": False},
        check_ok_status=False,
    )
    if response.status_code != 200:
        log.error(
            "GET /studies/%s/study-visits returned %d",
            study_uid,
            response.status_code,
        )
        return None

    visits = response.json().get("items", [])
    if not visits:
        return 0

    updated = 0
    for visit in visits:
        uid = visit.get("uid")
        order = visit.get("order")
        if uid is None or order is None:
            log.warning(
                "Visit entry missing uid or order in study %s — skipping: %s",
                study_uid,
                visit,
            )
            continue
        # Only the current visit node, not its superseded or locked/released versions
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_VISIT]->(sv:StudyVisit {uid: $uid})
            WHERE NOT (sv)<-[:BEFORE]-(:StudyAction)
            SET sv.order = $order
            """,
            {"study_uid": study_uid, "uid": uid, "order": order},
        )
        if summary.counters.contains_updates:
            updated += 1

    return updated


def assign_visit_order(db_driver, log) -> bool:
    """Assign `order` to all current (latest) StudyVisit nodes.

    For each study calls GET /studies/{uid}/study-visits and uses the API-computed
    ``order`` field (derived from TimelineAR) as the authoritative chronological
    position. This is idempotent: re-running overwrites existing values with the
    same result.

    Requires the API to be running and reachable. Raises after processing all studies
    if the API failed for any of them, so that the migration doesn't record success.
    """
    study_uids = _get_study_uids_with_visits(db_driver)
    log.info("Assigning order for %d studies via API", len(study_uids))

    total_updated = 0
    failed_study_uids = []
    for study_uid in study_uids:
        n = _assign_visit_order_for_study(db_driver, study_uid, log)
        if n is None:
            failed_study_uids.append(study_uid)
            continue
        total_updated += n
        log.debug("Study %s: updated %d visit nodes", study_uid, n)

    log.info("order assigned to %d visit nodes in total", total_updated)
    if failed_study_uids:
        raise RuntimeError(
            f"Could not assign visit order for {len(failed_study_uids)} studies: {failed_study_uids}"
        )
    return total_updated > 0


def remove_unit_definition_deprecated_properties(db_driver, log) -> bool:
    """Remove the deprecated `si_unit` and `legacy_code` properties from UnitDefinitionValue nodes."""
    log.info(
        "Removing `si_unit` and `legacy_code` properties from UnitDefinitionValue nodes"
    )

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.si_unit IS NOT NULL OR u.legacy_code IS NOT NULL
        REMOVE u.si_unit, u.legacy_code
        """,
    )
    print_counters_table(summary.counters)

    return summary.counters.contains_updates


def reset_conversion_factor_for_non_convertible_units(db_driver, log) -> bool:
    """Reset `conversion_factor_to_master` to null on non-convertible, non-master UnitDefinitionValue nodes."""
    log.info(
        "Resetting `conversion_factor_to_master` on non-convertible UnitDefinitionValue nodes"
    )

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.convertible_unit = false
          AND u.master_unit = false
          AND u.conversion_factor_to_master IS NOT NULL
        REMOVE u.conversion_factor_to_master
        """,
    )
    print_counters_table(summary.counters)

    return summary.counters.contains_updates


def rename_activity_item_class_display_name_to_label(db_driver, log) -> bool:
    """
    Rename the `display_name` property of ActivityItemClassValue nodes to `label`.

    Covers every version node, not only the LATEST one, so that the version history
    keeps its values. NonStandardVariableValue nodes carry the ActivityItemClassValue
    label too, so they are renamed by the same query.

    An existing `label` value is never overwritten.
    """
    log.info("Renaming ActivityItemClassValue.display_name to label")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (v:ActivityItemClassValue)
        WHERE v.display_name IS NOT NULL
        SET v.label = coalesce(v.label, v.display_name)
        REMOVE v.display_name
        """,
    )
    print_counters_table(summary.counters)

    return summary.counters.contains_updates


def convert_non_string_short_visit_labels(db_driver, log) -> bool:
    """
    Convert non-string `short_visit_label` values of Non and Unscheduled StudyVisit nodes to "V"-prefixed strings.

    Migration 008 set the label of Non and Unscheduled visits to the visit number as an integer.
    Correction 020 missed those that already had `show_visit = false`, as `STARTS WITH` on an integer is null.
    The labels are prefixed with "V", as correction 020 intended.
    """
    log.info(
        "Converting non-string short_visit_label values of Non and Unscheduled visits to strings"
    )

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (visit:StudyVisit)
        WHERE visit.visit_class IN ['NON_VISIT', 'UNSCHEDULED_VISIT']
            AND visit.short_visit_label IS NOT NULL
            AND NOT visit.short_visit_label IS :: STRING
        SET visit.short_visit_label = 'V' + toString(visit.short_visit_label)
        """,
    )
    print_counters_table(summary.counters)

    return summary.counters.contains_updates


def save_soa_snapshots_of_locked_and_released_study_versions(db_driver, log) -> bool:
    """
    Render and save the Protocol SoA and Protocol Lab table SoA snapshots of each LOCKED or RELEASED study version
    that has no StudySoASnapshot of the layout yet.

    The snapshot is a StudySoASnapshot node holding the HTML, DOCX, XLSX and JSON renderings of the SoA.
    The API renders it with POST /studies/{study_uid}/flowchart/snapshot. A Protocol SoA is rendered from the legacy
    HAS_PROTOCOL_SOA_CELL and HAS_PROTOCOL_SOA_FOOTNOTE relationships when the study version has them, so the frozen
    SoA stays as it is. Otherwise, and for the Protocol Lab table SoA, which was never frozen, it is built from the
    study selections of the study version.

    Every LOCKED study version also has a RELEASED HAS_VERSION relationship, and the API looks study versions up by
    the RELEASED ones. A study version that fails to render is logged and skipped, keeping its legacy relationships.
    """
    saved = 0
    for layout in SOA_SNAPSHOT_LAYOUTS:
        saved += _save_soa_snapshots_of_layout(db_driver, log, layout)
    return saved > 0


def _save_soa_snapshots_of_layout(db_driver, log, layout: str) -> int:
    """Saves the SoA snapshot of the layout for each LOCKED or RELEASED study version without it,
    and returns the number of saved snapshots"""
    log.info("Saving %s SoA snapshots of LOCKED and RELEASED study versions", layout)

    records, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[has_version:HAS_VERSION {status: 'RELEASED'}]->(study_value:StudyValue)
        WHERE NOT (study_value)-[:HAS_SOA_SNAPSHOT]->(:StudySoASnapshot {layout: $layout})
        WITH study_root, study_value, has_version
        ORDER BY has_version.start_date
        WITH study_root.uid AS study_uid, study_value, head(collect(has_version.version)) AS version
        RETURN study_uid, version
        ORDER BY study_uid, version
        """,
        {"layout": layout},
    )

    failed = []
    for record in records:
        study_uid, version = record["study_uid"], record["version"]
        try:
            api_post(
                f"/studies/{study_uid}/flowchart/snapshot",
                {},
                params={"study_value_version": version, "layout": layout},
                timeout=SOA_SNAPSHOT_TIMEOUT_SECONDS,
            )
        except (AssertionError, httpx.HTTPError) as exc:
            log.error(
                "Failed to save %s SoA snapshot of study %s version %s: %s",
                layout,
                study_uid,
                version,
                exc,
            )
            failed.append((study_uid, version))

    log.info(
        "Saved %d %s SoA snapshots, %d failed: %s",
        len(records) - len(failed),
        layout,
        len(failed),
        failed,
    )

    return len(records) - len(failed)


def remove_legacy_protocol_soa_cell_relationships(db_driver, log) -> bool:
    """
    Remove the HAS_PROTOCOL_SOA_CELL and HAS_PROTOCOL_SOA_FOOTNOTE relationships that the StudySoASnapshot nodes replace.

    Relationships are only removed from StudyValue nodes that have a Protocol SoA snapshot already,
    and from StudyValue nodes not belonging to any LOCKED or RELEASED study version, where they were left over.
    """
    log.info(
        "Removing legacy HAS_PROTOCOL_SOA_CELL and HAS_PROTOCOL_SOA_FOOTNOTE relationships"
    )

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_value:StudyValue)-[legacy:HAS_PROTOCOL_SOA_CELL|HAS_PROTOCOL_SOA_FOOTNOTE]->()
        WHERE (study_value)-[:HAS_SOA_SNAPSHOT]->(:StudySoASnapshot {layout: 'protocol'})
            OR NOT (:StudyRoot)-[:HAS_VERSION {status: 'RELEASED'}]->(study_value)
        CALL {
            WITH legacy
            DELETE legacy
        } IN TRANSACTIONS OF 10000 ROWS
        """,
    )
    print_counters_table(summary.counters)

    return summary.counters.contains_updates


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    with SchemaMigrationNode(filename=__file__, driver=DB_DRIVER):
        ### Fail before changing anything when the SEMTCDT or CODMDT codelist is missing
        check_datatype_codelists(DB_DRIVER, logger)

        ### Common migrations
        migrate_indexes_and_constraints(DB_CONNECTION, logger)

        ### Release specific migrations
        uppercase_project_numbers(DB_DRIVER, logger)
        change_catalogue_of_datatype_codelist(DB_DRIVER, logger)
        migrate_feature_flags_to_root_value(DB_DRIVER, logger)
        link_sponsor_model_values_to_library(DB_DRIVER, logger)
        link_dataset_variable_to_data_model_catalogue(DB_DRIVER, logger)

        ### Publish Sponsor Model field-schema versions, then link existing
        ### sponsor models to the schema version they follow
        load_sponsor_model_schemas(logger)
        link_sponsor_model_values_to_schema(DB_DRIVER, logger)

        ### Move is_ordinal and codelist_type from attributes to name values
        move_codelist_properties_to_name_value(DB_DRIVER, logger)

        ### Mark STRESC codelists as ordinal, and set ordinal on their terms
        ### (MUST run AFTER move_codelist_properties_to_name_value)
        set_ordinal_for_stresc_codelists(DB_DRIVER, logger)

        ### Ensure Archived library exists (libraries API)
        ensure_archived_library(logger)

        ### Pre-create MetaStudyField nodes from CTConfigValue data (MUST run before remove_ct_config_nodes)
        migrate_meta_study_fields(DB_DRIVER, logger)

        ### Remove CT config nodes (MUST run AFTER migrate_meta_study_fields)
        remove_ct_config_nodes(DB_DRIVER, logger)

        ### Control Type single-select -> multi-select (MUST run AFTER migrate_meta_study_fields)
        migrate_control_type_to_array_field(DB_DRIVER, logger)

        ### ODM Item data type from str to rel
        migrate_odm_item_datatype_to_ct_term(DB_DRIVER, logger)
        remove_odm_item_datatype_string_property(DB_DRIVER, logger)

        ### Remove deprecated properties and reset conversion factors for UnitDefinitionValue nodes
        remove_unit_definition_deprecated_properties(DB_DRIVER, logger)
        reset_conversion_factor_for_non_convertible_units(DB_DRIVER, logger)

        ### Rename ActivityItemClassValue.display_name to label
        rename_activity_item_class_display_name_to_label(DB_DRIVER, logger)

        ### Convert non-string short_visit_label values of Non and Unscheduled visits to strings
        ### (MUST run BEFORE save_soa_snapshots_of_locked_and_released_study_versions)
        convert_non_string_short_visit_labels(DB_DRIVER, logger)

        ### Migrate all SPECIAL_VISIT nodes to SINGLE_VISIT
        ### (MUST run BEFORE save_soa_snapshots_of_locked_and_released_study_versions, the rendered SoA contains visits)
        migrate_special_visits_to_single_visit(DB_DRIVER, logger)

        ### Assign order to all current StudyVisit nodes
        ### (MUST run AFTER migrate_special_visits_to_single_visit and BEFORE the SoA snapshots)
        assign_visit_order(DB_DRIVER, logger)

        ### Store rendered Protocol and Protocol Lab table SoA of LOCKED and RELEASED study versions on StudySoASnapshot nodes (flowchart API)
        save_soa_snapshots_of_locked_and_released_study_versions(DB_DRIVER, logger)

        ### Remove legacy SoA snapshot relationships
        ### (MUST run AFTER save_soa_snapshots_of_locked_and_released_study_versions)
        remove_legacy_protocol_soa_cell_relationships(DB_DRIVER, logger)


if __name__ == "__main__":
    main()
