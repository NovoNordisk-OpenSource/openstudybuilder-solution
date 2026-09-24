# Release 2.9 (x 2026)

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

### 1. Add section and feature properties to FeatureFlags
-------------------------------------
#### Change description
- Add a `section` property to all `FeatureFlag` nodes with default value being `'admin'`
- Add a `feature` property to all `FeatureFlag` nodes with default value being `'FIXME'`

#### Nodes affected
- `FeatureFlag`

#### Relationships affected
- None