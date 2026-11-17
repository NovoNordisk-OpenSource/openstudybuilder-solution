# Release 2.10 & 2.11 (x 2026)

## Prerequisites

The sponsor codelists `SEMTCDT` (Semantic Data Type) and `CODMDT` (CDISC ODM Data Type)
must be in the database before this migration runs. A database created before release 2.10,
such as prod, does not have them. Load them with the `import_sponsor_data` `codelistterms2`
step, which reads `sponsor_codelist_definitions.csv` and `datatype.csv` from
`import_sponsor_data/datafiles/sponsor_library/`.

The migration checks this before changing any data, and fails (`result=FAILED`) when:
- `CTConfigValue` study fields remain and `SEMTCDT` lacks any of the terms step 7 links to
  (`boolean`, `ctTerm`, `datetime`, `durationDatetime`, `integer`, `text`), or
- `OdmItemValue` nodes still carry a `datatype` string and `CODMDT` is missing.

Without `SEMTCDT`, step 7 would create no `MetaStudyField`, and step 8 would then delete the
`CTConfig` nodes step 7 reads from, so the step could not be repeated on that database.

## Common migrations

### 1. Indexes and Constraints
-------------------------------------
#### Change Description
- Re-create all db indexes and constraints according to [db schema definition](../../db/db_schema.py).


## Release specific migrations

### 1. Uppercase project_number property of Project nodes
-------------------------------------
#### Change description
- Update all `Project` nodes update `project_number` property to upper where it is not null or already uppercased.
#### Nodes affected
- `Project`
#### Relationships affected
- None


### 2. Change Catalogue of DATATYPE Codelist
-------------------------------------
#### Change description
- Removed relationship to `DATATYPE` codelist from `SDTM CT` catalogue
- Added relationship to `DATATYPE` codelist from `DDF CT` catalogue
#### Nodes affected
N/A
#### Relationships affected
- HAS_CODELIST


### 3. Move is_ordinal and codelist_type from CTCodelistAttributesValue to CTCodelistNameValue
-------------------------------------
#### Change description
- Copy `is_ordinal` and `codelist_type` properties from the LATEST `CTCodelistAttributesValue` to all related `CTCodelistNameValue` versions (defaults: `is_ordinal=false`, `codelist_type='Standard'`).
- Remove `is_ordinal` and `codelist_type` properties from all `CTCodelistAttributesValue` nodes.
#### Nodes affected
- `CTCodelistAttributesValue`
- `CTCodelistNameValue`
#### Relationships affected
- None

### 4. Migrate FeatureFlag flat nodes to Root/Value
-------------------------------------
#### Change description
- For each `:FeatureFlag`, create `FeatureFlagRoot` + `FeatureFlagValue` with
  `LATEST`, `LATEST_FINAL`, and open `HAS_VERSION` (`status: Final`, `version: 1.0`).
- Assign `uid` via `FeatureFlagCounter` (`FeatureFlag_xxxxxx`).
- Run account assessment (counts + field equality + open version / LATEST_FINAL).
- Delete old `:FeatureFlag` nodes only after assessment passes.

#### Nodes affected
- `FeatureFlag` (removed)
- `FeatureFlagRoot` (created)
- `FeatureFlagValue` (created)
- `Counter` / `FeatureFlagCounter`

#### Relationships affected
- `HAS_VERSION`, `LATEST`, `LATEST_FINAL` (created)

### 5. Link SponsorModelValue nodes to the "Sponsor" Library
-------------------------------------
#### Change description
- Previously, a Sponsor Model's library was implicitly taken from the library of
  the (shared) Implementation Guide root it extends (e.g. `SDTMIG` -> `CDISC`),
  which is incorrect since a sponsor model is always sponsor-owned content.
- For each `SponsorModelValue` node without an existing library link, create a
  `CONTAINS_SPONSOR_MODEL` relationship from the `Sponsor` `Library` node (default, fix if you need
  a different Library for your models).
- Idempotent: nodes that already have a `CONTAINS_SPONSOR_MODEL` link (e.g. from
  a prior partial run) are left untouched and skipped.

#### Nodes affected
- `SponsorModelValue` (unchanged, only new relationship)
- `Library` (unchanged, only new relationship)

#### Relationships affected
- `CONTAINS_SPONSOR_MODEL` (created)

### 6. Link DatasetVariable nodes to  "SDTMIG" DataModelCatalogue
-------------------------------------
#### Change description
- An issue in the Sponsor Model import process introduced DatasetVariables nodes
  without a relationship to any DataModelCatalogue nodes
- For each `DatasetVariable` node without an existing relationship to `DataModelCatalogue`,
  create a `HAS_DATASET_VARIABLE` relationship to `SDTMIG`. This is safe because all of
  these orphan nodes were created in a Sponsor Model

#### Nodes affected
- `DatasetVariable` (unchanged, only new relationship)

#### Relationships affected
- `HAS_DATASET_VARIABLE` (created)


### 7. Pre-create `MetaStudyField` nodes linked to Semantic Data Type terms
-------------------------------------
#### Change description
- Reads `study_field_name` and `study_field_data_type` from the existing
  `CTConfigValue` nodes (skipping `*_null_value_code` placeholders).
- For each unique non-null study field, MERGEs a `MetaStudyField` node and
  links it to the matching CTTerm in the **SEMTCDT** (Semantic Data Type)
  codelist via:
  ```
  (MetaStudyField {osb_field_name: <study_field_name>,
                   osb_page_reference: <page_reference>})
      -[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
      -[:HAS_SELECTED_TERM]->(:CTTermRoot)   // SEMTCDT term
  ```
- The `study_field_data_type` is mapped to a SEMTCDT `code_submission_value` as follows:

  | study_field_data_type | SEMTCDT submission_value |
  | --- | --- |
  | `text`, `registry`, `project` | `text` |
  | `int` | `integer` |
  | `bool` | `boolean` |
  | `date` | `datetime` |
  | `time` | `durationDatetime` |
  | `multiselect` | `ctTerm` |

- **Override for CTTerm-backed text fields**: text-typed fields with a
  `(:StudyField)-[:HAS_TYPE]->(:CTTermContext)` relationship use `ctTerm`.
- **`osb_page_reference`** is set from `CTConfigValue.study_field_grouping`.
- Idempotent: fields already linked are skipped.
- Fails when a SEMTCDT term it needs is missing (see [Prerequisites](#prerequisites)).
- **Must run BEFORE step 8** (`CTConfigValue` removal).

#### Nodes affected (created)
- `MetaStudyField`
- `CTTermContext`

#### Relationships affected (created)
- `(MetaStudyField)-[:HAS_SEMANTIC_DATA_TYPE]->(CTTermContext)`
- `(CTTermContext)-[:HAS_SELECTED_TERM]->(CTTermRoot)`


### 8. Remove CTConfigRoot and CTConfigValue nodes
-------------------------------------
#### Change description
- Delete all `CTConfigRoot` and `CTConfigValue` nodes from the database, including all relationships attached to them.
- These nodes are no longer needed as study fields configuration is now managed outside of the graph database.
- **Must run AFTER step 7** (`MetaStudyField` pre-creation).
- Refuses to delete anything while a study field with a mapped `study_field_data_type` has no
  `MetaStudyField` linked to a semantic data type.

#### Nodes affected
- `CTConfigRoot`
- `CTConfigValue`

#### Relationships affected
- All relationships connected to `CTConfigRoot` and `CTConfigValue` nodes are removed via `DETACH DELETE`.


### 8a. Convert Control Type study field from single-select to multi-select
-------------------------------------
#### Change description
- Control Type (Study Properties → Study Attributes) can now hold multiple CT terms, so the
  study field is renamed `control_type_code` → `control_type_codes` (the plural `_codes`
  convention of every other multi-select study field) and stored as an array field.
- Every `StudyTextField {field_name: 'control_type_code'}` is converted **in place** into a
  `StudyArrayField {field_name: 'control_type_codes'}`:
  - `value` becomes a list with the selected CT term uid (taken from the `HAS_TYPE` term
    when present), or `[]` when the field only carries a null flavor.
  - `HAS_TEXT_FIELD` relationships from `StudyValue` nodes are replaced with `HAS_ARRAY_FIELD`.
  - `HAS_TYPE`, `HAS_REASON_FOR_NULL_VALUE` and audit trail `BEFORE`/`AFTER` relationships stay
    attached, so all study versions and the field audit trail are preserved.
- `MetaStudyField {osb_field_name: 'control_type_code'}` is renamed to `control_type_codes`.
- The Trial Summary parameter linked to that `MetaStudyField` (TCNTRL) gets `cardinality = 'Many'`.
- **Must run AFTER step 7** (`MetaStudyField` pre-creation reads the not-yet-converted field).
- Idempotent: nothing matches once converted.

#### Nodes affected
- `StudyTextField` → `StudyArrayField` (label swapped, `field_name` and `value` updated)
- `MetaStudyField` (`osb_field_name` renamed)
- `CTTermNameValue` (`cardinality` set to `Many`)

#### Relationships affected
- `HAS_TEXT_FIELD` (removed) → `HAS_ARRAY_FIELD` (created)


### 9. Publish Sponsor Model field-schema versions and link existing Sponsor Models to them
-------------------------------------
#### Change description
- Publishes every Sponsor Model field-schema version found under
  [import_sponsor_data/datafiles/sponsor_library/sponsormodel/schemas](../../import_sponsor_data/datafiles/sponsor_library/sponsormodel/schemas)
  (e.g. `sponsor.v1.yaml`, `sponsor.v2.yaml`) via `POST /standards/sponsor-models/schema`,
  the same way `run_import_sponsormodels.py`'s `handle_schemas()` does. Skips any
  `(library_name, schema_version)` that is already published (checked via `GET`
  first), since a re-publish of identical content returns `200`, not the `201`
  the migration's `api_post()` helper requires.
- For each sponsor model folder with a `model_info.json` under
  [import_sponsor_data/datafiles/sponsor_library/sponsormodel](../../import_sponsor_data/datafiles/sponsor_library/sponsormodel)
  (the same file `run_import_sponsormodels.py` uses to build the sponsor model),
  connects its `SponsorModelValue` node (matched by `sponsor_model_name`) to the
  `SponsorModelSchemaValue` for the `library_name`/`schema_version` it declares,
  via a `FOLLOWS_SCHEMA` relationship - the same link
  `SponsorModelRepository._link_schema_version()` creates for newly-created
  sponsor models. Idempotent: nodes that already have a `FOLLOWS_SCHEMA` link
  are left untouched and skipped.

#### Nodes affected
- `SponsorModelSchemaRoot` / `SponsorModelSchemaValue` (created via the API)
- `SponsorModelValue` (unchanged, only new relationship)

#### Relationships affected
- `HAS_SCHEMA_VERSION` (created via the API)
- `FOLLOWS_SCHEMA` (created)


### 10. Mark STRESC codelists as ordinal and set ordinal on their terms
-------------------------------------
#### Change description
- CDISC codelists whose name contains "STRESC" are the
  "standardized character result" codelists: their terms are often the same integer-like
  values as the corresponding STRESN (standardized numeric result) codelist, encoded as
  strings, plus a few non-numeric catch-all terms such as `UNKNOWN` or `N/A`. Some STRESC
  codelists however only ever have non-numeric terms (e.g. free-text response codelists),
  and must NOT be treated as ordinal.
- For every `CTCodelistNameValue` matched by
  `MATCH (cr:CTCodelistRoot)--(cnr:CTCodelistNameRoot)--(cnv:CTCodelistNameValue) WHERE cnv.name CONTAINS "STRESC"`,
  sets `is_ordinal = true` **only if** at least one of the codelist's terms (`(cr)-[:HAS_TERM]->(:CTCodelistTerm)`)
  has an integer `submission_value` (or a numeric string, e.g. `"1"`).
- For every `HAS_TERM` relationship from such an (ordinal) codelist's root to a `CTCodelistTerm`, sets
  `ordinal` to the term's `submission_value` converted to an integer (stored as a float, to
  match the `ordinal` `FloatProperty`), or leaves it unset (`null`) when the `submission_value`
  is not an integer (e.g. `UNKNOWN`, `N/A`).
- **Must run AFTER step 3** (`move_codelist_properties_to_name_value`), since `is_ordinal` must
  already live on `CTCodelistNameValue` by the time this runs.
- Idempotent: only touches `CTCodelistNameValue` nodes not already flagged, and only rewrites a
  `HAS_TERM.ordinal` when the computed value differs from what's already stored.

#### Nodes affected
- `CTCodelistNameValue` (`is_ordinal` set to `true`)

#### Relationships affected
- `HAS_TERM` (`ordinal` property set)

### 11. Migrate all SPECIAL_VISIT nodes to SINGLE_VISIT
-------------------------------------
#### Change Description
All `StudyVisit` nodes with `visit_class = 'SPECIAL_VISIT'` are converted to `'SINGLE_VISIT'`.
Each converted visit receives:
- `visit_suffix` — letter derived from its position among siblings sharing the same anchor (`A, B, C…` for non-ED; `X, Y, Z` for ED).
- `HAS_TIMEPOINT` — attached to the `TimePointRoot` for 0 days / Global anchor visit.
- `expected_time_value` — the timing of the anchor visit (read from the API, in the unit of the timepoint),
  so that the visit stays next to its anchor visit. Not set for Early discontinuation visits, which follow their parent visit.

All version nodes of a visit that were special visits are converted, also the ones that only belong to locked
or released study versions. Visits that are no longer current in the latest study version (deleted, or of a
deleted study) get the suffix and the 0 days timepoint, but no `expected_time_value`.

The visit type (`HAS_VISIT_TYPE`) and `visit_sublabel_reference` (the old anchor visit) of converted
visits are left untouched. A temporary `_migrating` marker lets a re-run complete a failed conversion.

#### Nodes Affected
- `StudyVisit` — `visit_class`, `visit_suffix`, `expected_time_value` updated

#### Relationships Affected
- `(StudyVisit)-[:HAS_TIMEPOINT]->` — added

#### Prerequisites
- At least one study with a global anchor visit must exist.
- The API must be running. This step and step 12 read from the API, so they run last, after the DB-only steps.

### 12. Assign `order` to all current StudyVisit nodes
-------------------------------------
#### Change Description
The visit's chronological position was derived in memory but never persisted. This migration
writes it to every current `StudyVisit` node's `order` property (inherited from the
`StudySelection` base class) by calling `GET /studies/{uid}/study-visits` per study and reading
the `order` field from the response. Only the visit nodes of the latest study version are updated.
If the API call fails for any study, the migration fails after processing the other studies.

#### Nodes Affected
- `StudyVisit` — `order` property populated

#### Prerequisites
- Must run after step 11.


### 11. Migrate ODM Item datatype from string property to CT term relationship
-------------------------------------
#### Change description
The datatype of ODM Item is changed to be represented as a CT term relationship instead of a plain string property on the value node.
This migration brings existing DB data in line with the new model.

Two steps are performed:

**Step 1 - Create `HAS_DATA_TYPE` relationships**
For each `OdmItemValue` node that carries a `datatype` string property:
- The stored string (e.g. `"text"`, `"integer"`, `"float"`) is matched case-insensitively
  against `CTCodelistTerm.submission_value` inside the `CODMDT` codelist (DDF CT).
- A `CTTermContext` node is merged (reused if it already exists for the same
  codelist/term pair) with outgoing `HAS_SELECTED_CODELIST` and `HAS_SELECTED_TERM`
  relationships.
- A `HAS_DATA_TYPE` relationship is created from the `OdmItemValue` to the `CTTermContext`.

**Step 2 - Remove the legacy `datatype` string property**
After all relationships are in place, the `datatype` property is removed from every
`OdmItemValue` node where it is still present.

#### Nodes affected
- `OdmItemValue` - `datatype` string property removed
- `CTTermContext` - new nodes may be created (one per unique codelist/term pair)

#### Relationships affected
- `HAS_DATA_TYPE` - created between `OdmItemValue` and `CTTermContext`
- `HAS_SELECTED_CODELIST` - created on new `CTTermContext` nodes (if not already present)
- `HAS_SELECTED_TERM` - created on new `CTTermContext` nodes (if not already present)


### 12. Remove deprecated properties and reset conversion factor for UnitDefinitionValue nodes
-------------------------------------
#### Change description
- Removes the deprecated `si_unit` and `legacy_code` properties from every `UnitDefinitionValue` node.
- Resets `conversion_factor_to_master` to `null` on `UnitDefinitionValue` nodes that are neither
  convertible (`convertible_unit = false`) nor a master unit (`master_unit = false`), since such a
  conversion factor is meaningless for non-convertible, non-master units.
- Master units keep their `conversion_factor_to_master` (typically `1.0`) untouched.
- Idempotent: only touches nodes still carrying the deprecated properties, or a stale conversion
  factor.

#### Nodes affected
- `UnitDefinitionValue` (`si_unit` and `legacy_code` removed; `conversion_factor_to_master` reset
  where applicable)

#### Relationships affected
- None

### 13. Rename display_name property of ActivityItemClassValue nodes to label
-------------------------------------
#### Change description
- On every `ActivityItemClassValue` node (all versions, not only `LATEST`), move the `display_name`
  property to `label` and remove `display_name`.
- `NonStandardVariableValue` nodes also carry the `ActivityItemClassValue` label, so they are
  renamed by the same step.
- An existing `label` value is never overwritten.
- Idempotent: only touches nodes still carrying `display_name`.

#### Nodes affected
- `ActivityItemClassValue` (`display_name` renamed to `label`)
- `NonStandardVariableValue` (`display_name` renamed to `label`)

#### Relationships affected
- None

### 13a. Convert non-string short_visit_label of Non and Unscheduled StudyVisit nodes to strings
-------------------------------------
#### Change description
- Migration 008 set `short_visit_label` of Non and Unscheduled visits to the visit number as an integer
  (`29999`, `29500`). Correction 020 prefixed them with "V", but missed those that already had
  `show_visit = false`, as `STARTS WITH` on an integer evaluates to null.
- The API reads `short_visit_label` as a string, so rendering the SoA of a study version with such a visit
  fails with a validation error.
- Converts every non-string `short_visit_label` of a `NON_VISIT` or `UNSCHEDULED_VISIT` to a string prefixed
  with "V", as correction 020 intended (`29500` → `"V29500"`). Visits of other classes are left unchanged.
- Must run before step 14, which renders the SoA of locked and released study versions.
- Idempotent: once converted, no non-string labels are left.

#### Nodes affected
- `StudyVisit` (property `short_visit_label` updated)

#### Relationships affected
- None

### 14. Store the Protocol SoA and Protocol Lab table SoA of locked and released study versions as rendered documents
-------------------------------------
#### Change description
- The Protocol SoA and the Protocol Lab table SoA of a LOCKED or RELEASED study version are now stored as
  `StudySoASnapshot` nodes, one per layout, each holding the complete HTML, DOCX, XLSX and JSON renderings.
  Previously the Protocol SoA was kept as `HAS_PROTOCOL_SOA_CELL` and `HAS_PROTOCOL_SOA_FOOTNOTE` relationships from
  which the API rebuilt the SoA on every request, and the Protocol Lab table SoA was always built on request.
  The flowchart endpoints return the stored rendering of a locked or released study version as it is,
  so later changes to the data model or to the API code no longer change it, and need no data migration.
- For every LOCKED or RELEASED study version without a `StudySoASnapshot` node of the layout, for the layouts
  `protocol` and `protocol_lab_table`, the migration calls
  `POST /studies/{study_uid}/flowchart/snapshot?study_value_version={version}&layout={layout}`.
  - A Protocol SoA is rendered from the legacy `HAS_PROTOCOL_SOA_CELL` and `HAS_PROTOCOL_SOA_FOOTNOTE` relationships
    when the study version has them, so the stored SoA is identical to the one shown before the migration.
  - Otherwise, and always for the Protocol Lab table SoA, the SoA is built from the study selections of the study
    version, so it reflects the data of the study version as it is at the time of the migration.
- A snapshot that fails to render (an error response, a timeout after 600 seconds or a connection error) is logged
  and skipped; a study version keeps its legacy relationships when its Protocol SoA fails. Rendering is retried by
  re-running the migration or by calling the endpoint above. After a timeout the API may still finish saving the
  snapshot; a re-run then skips it.
- Idempotent: only study versions without a `StudySoASnapshot` node of the layout are rendered.

#### Nodes affected
- `StudySoASnapshot` (created, properties `layout`, `html`, `docx`, `xlsx`, `json`, `time_unit`, `created_at`)
- `UpdateSoASnapshot` (created, audit trail entry of each saved snapshot)

#### Relationships affected
- `(:StudyValue)-[:HAS_SOA_SNAPSHOT]->(:StudySoASnapshot)` (created)

### 15. Remove legacy Protocol SoA snapshot relationships
-------------------------------------
#### Change description
- Must run after step 14.
- Deletes the `HAS_PROTOCOL_SOA_CELL` and `HAS_PROTOCOL_SOA_FOOTNOTE` relationships of `StudyValue` nodes that
  have a Protocol SoA `StudySoASnapshot` node, and of `StudyValue` nodes not belonging to any LOCKED or RELEASED
  study version, where they were left over.
- Idempotent: once deleted, there is nothing left to delete.
- Follow-up: the API code that rendered the SoA from these relationships is kept for this release only, so that
  this migration can render existing study versions from them. It is marked with `LEGACY-SOA-SNAPSHOT (242942)`;
  remove it in the next release: `grep -rn LEGACY-SOA-SNAPSHOT api/ verifications/`.

#### Nodes affected
- None

#### Relationships affected
- `HAS_PROTOCOL_SOA_CELL` (deleted)
- `HAS_PROTOCOL_SOA_FOOTNOTE` (deleted)
