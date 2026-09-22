"""Schema migrations needed to release 2.10 & 2.11 in PROD"""

import json
import os

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
        log.warning(
            "SEMTCDT submission_values not found in DB: %s",
            sorted(missing_semtcdt_terms),
        )

    return contains_updates


def remove_ct_config_nodes(db_driver, log) -> bool:
    """Remove all CTConfigRoot and CTConfigValue nodes."""
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


def migrate_odm_item_datatype_to_ct_term(db_driver, log) -> bool:
    """
    For each OdmItemValue node that still carries the legacy `datatype` string property
    and has no HAS_DATA_TYPE relationship, look up the matching CT term in the CODMDT
    codelist, create (or reuse) a CTTermContext node, and connect the OdmItemValue to it
    via HAS_DATA_TYPE.

    The lookup is case-insensitive so that values stored as e.g. "Text" or "TEXT" are
    matched correctly against CTCodelistTerm.submission_value.

    Nodes/relationships that already have HAS_DATA_TYPE are left untouched.
    """
    log.info(
        "Migrating OdmItemValue.datatype string property to HAS_DATA_TYPE relationship"
    )
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
    return summary.counters.contains_updates


def remove_odm_item_datatype_string_property(db_driver, log) -> bool:
    """
    Remove the legacy `datatype` string property from all OdmItemValue nodes.

    This must run after migrate_odm_item_datatype_to_ct_term so that no data is
    lost before the CT term relationships are in place.
    """
    log.info("Removing legacy `datatype` string property from OdmItemValue nodes")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (oiv:OdmItemValue)
        WHERE oiv.datatype IS NOT NULL
        REMOVE oiv.datatype
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


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


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    with SchemaMigrationNode(filename=__file__, driver=DB_DRIVER):
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

        ### ODM Item data type from str to rel
        migrate_odm_item_datatype_to_ct_term(DB_DRIVER, logger)
        remove_odm_item_datatype_string_property(DB_DRIVER, logger)

        ### Remove deprecated properties and reset conversion factors for UnitDefinitionValue nodes
        remove_unit_definition_deprecated_properties(DB_DRIVER, logger)
        reset_conversion_factor_for_non_convertible_units(DB_DRIVER, logger)


if __name__ == "__main__":
    main()