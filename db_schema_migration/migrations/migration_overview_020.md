# Release: 2.6 (x 2026)

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

### 1. Add codelist_type property to Codelists
-------------------------------------
#### Change Description
- Add a `codelist_type` property to all `CTCodelistAttributesValue` nodes where the property is missing.
- The default value is `"Standard"`.

#### Nodes Affected
- `CTCodelistAttributesValue`

#### Relationships affected
- None


### 2. Migrate Sponsor Model ordinal from string to integer
-------------------------------------
#### Change Description
- Convert the `ordinal` property stored on Sponsor Model relationships from a string type to an integer type.
- Affects the `HAS_DATASET` relationship linking `SponsorModelValue` to `SponsorModelDatasetInstance`.
- Affects the `HAS_DATASET_VARIABLE` relationship linking `SponsorModelDatasetInstance` to `SponsorModelDatasetVariableInstance`.

#### Nodes Affected
- None (property is on relationships)

#### Relationships affected
- `(:SponsorModelValue)-[:HAS_DATASET {ordinal}]->(:SponsorModelDatasetInstance)`
- `(:SponsorModelDatasetInstance)-[:HAS_DATASET_VARIABLE {ordinal}]->(:SponsorModelDatasetVariableInstance)`
