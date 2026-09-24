# Release 2.8 (x 2026)

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

### 2. Split ActivityInstance data into grouping model
-------------------------------------
#### Change Description
- For each `ActivityInstanceRoot` -> `ActivityInstanceValue` pair with direct
  `HAS_ACTIVITY` links and no `HAS_GROUPING_ROOT`,
  create a new `ActivityInstanceGroupingRoot` and `ActivityInstanceGroupingValue`.
- Copy existing direct relationships (type and properties) from 
  `ActivityInstanceRoot` -> `ActivityInstanceValue`
  to `ActivityInstanceGroupingRoot` -> `ActivityInstanceGroupingValue`.
- Move all `HAS_ACTIVITY` relationships from `ActivityInstanceValue` to `ActivityInstanceGroupingValue`.

#### Nodes Affected
- `ActivityInstanceRoot`
- `ActivityInstanceValue`
- `ActivityInstanceGroupingRoot`
- `ActivityInstanceGroupingValue`
- `ActivityGrouping`

#### Relationships affected
- `HAS_GROUPING_ROOT`
- `HAS_ACTIVITY`
- Dynamic relationship types copied from `(:ActivityInstanceRoot)-[rel]->(:ActivityInstanceValue)` to 
  `(:ActivityInstanceGroupingRoot)-[rel]->(:ActivityInstanceGroupingValue)` with relationship properties preserved.
