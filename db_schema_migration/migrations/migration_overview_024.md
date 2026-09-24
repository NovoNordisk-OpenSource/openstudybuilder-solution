# Release 2.10 & 2.11 (x 2026)

## Common migrations

### 1. Indexes and Constraints
-------------------------------------
#### Change Description
- Re-create all db indexes and constraints according to [db schema definition](../../db/db_schema.py).


### 2. CT Config Values (Study Fields Configuration)
-------------------------------------
#### Change Description
- Re-create all `CTConfigValue` nodes according to values defined in [this file](../../import_sponsor_data/datafiles/configuration/study_fields_configuration.csv).

#### Nodes Affected
- CTConfigValue


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

#### Nodes affected
- `CTConfigRoot`
- `CTConfigValue`

#### Relationships affected
- All relationships connected to `CTConfigRoot` and `CTConfigValue` nodes are removed via `DETACH DELETE`.
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