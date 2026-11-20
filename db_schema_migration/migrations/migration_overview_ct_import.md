# Release 2.12 (x 2026)

## Common migrations

### 1. Indexes and Constraints
-------------------------------------
#### Change Description
- Re-create all db indexes and constraints according to [db schema definition](../../db/db_schema.py).
  This includes the CDISC staging indexes and constraints, so they are in place in the MDR database
  before the staging data is copied into it (step 2 below).


## Release specific migrations

Merge of the CDISC staging database into the MDR database. Step 1 renames relationship types and node labels in the
**staging** database (`STAGING_DATABASE_NAME`), step 2 copies the result into the **MDR** database
(`DATABASE_NAME`) and adds the `:CDISCStaging` label to every copied node.

If `STAGING_DATABASE_NAME`/`STAGING_DATABASE_URL` resolve to the MDR database itself, there is nothing to merge:
the **whole migration is skipped** (no schema changes, no `SchemaMigration` node).

**Prerequisites**
- Stop the standards-import application (and anything else writing to the staging database) before running.
- Take a backup of both databases.
- Set `STAGING_DATABASE_NAME` (and `STAGING_DATABASE_URL`, when the staging database lives on another
  server than `DATABASE_URL`).
- APOC must be available in the MDR database.

### 1. Rename staging relationship types and node labels
-------------------------------------
#### Change description
- Relationship types cannot be changed in place in Neo4j. For each entry in `REL_TYPE_RENAMES`
  every relationship is re-created with the new type (all properties preserved) and the old one deleted,
  in batches of 10 000.
- For each entry in `LABEL_RENAMES` the old label is removed and the new one set on every node carrying it,
  in batches of 10 000. Properties and relationships of those nodes are untouched.
- Both sub-steps fail if anything with an old type/label remains.
- Idempotent: renamed relationships/nodes no longer match, so a re-run (or a run resumed after a failure) is a no-op.
- Runs on the staging database, so it must run BEFORE step 2.

| Old relationship type | New relationship type |
| --- | --- |
| `HAS_TERM` | `HAS_GROUPED_TERM_MEMBER` |
| `HAS_VERSION` | `HAS_STAGED_VERSION` |
| `CONTAINS` | `DM_CONTAINS` |

| Old node label | New node label |
| --- | --- |
| `Version` | `DataModelStagingVersion` |

#### Nodes affected
- `Version` (label renamed to `DataModelStagingVersion`, in the staging database only)

#### Relationships affected
- `HAS_TERM`, `HAS_VERSION`, `CONTAINS` (type renamed, in the staging database only)


### 2. Copy the staging database into the MDR database, adding the `:CDISCStaging` label
-------------------------------------
#### Change description
- All staging nodes (with their labels and properties) and all staging relationships (with their type and
  properties) are streamed out of the staging database and created in the MDR database in batches
  (`UNWIND`, grouped by label set / relationship type, 10 000 rows per transaction; override with
  `STAGING_COPY_BATCH_SIZE`).
- Every copied node additionally receives the `:CDISCStaging` marker label, so the staging database itself is not
  modified by the labelling.
- Copied nodes are temporarily tagged with the label `__StagingMigration` and the property `__src_id`
  (the staging `elementId`), backed by a temporary unique constraint, so relationships can be attached to the
  right nodes in an efficient way. Afterwards the label and property are removed (`apoc.periodic.iterate`) and the constraint dropped.
- Indexes and constraints for the staging labels already exist at this point (common migration 1) and are
  enforced while loading.
- No label or relationship type of the staging database is used by the MDR data, so the two graphs are
  disjoint and no relationship connects them.
- Node and relationship counts are verified after the copy; any mismatch fails the migration.
- Re-run behaviour:
  - MDR already holds exactly as many `:CDISCStaging` nodes and relationships as staging: the step is skipped.
  - MDR holds a different number, or leftover `__StagingMigration` nodes (interrupted copy): the migration aborts
    without writing. Remove the partial data with `db/clear_staging.py` (pointed at the MDR database) and re-run.

#### Nodes affected
- All `:CDISCStaging` nodes (created in the MDR database)

#### Relationships affected
- All relationships between `:CDISCStaging` nodes (created in the MDR database)
