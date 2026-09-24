# Release: 2.x.x (x 202x)

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


### 3. Migrate grouping model for activities and subgroups
#### Change Description
- Remove the `ActivityValidGroup` nodes and instead link `ActivityGrouping` nodes
  directly to the `ActivityGroupValue` and `ActivitySubGroupValue` nodes
  via `HAS_SELECTED_GROUP` and `HAS_SELECTED_SUBGROUP` relationships.
- Remove the `ActivityValidGroupCounter` node.

#### Nodes Affected
- `ActivityValidGroup`
- `ActivityGrouping`
- `ActivitySubGroupValue`
- `ActivityGroupValue`
- `ActivityValidGroupCounter`

#### Relationships affected
- `HAS_SELECTED_GROUP`
- `HAS_SELECTED_SUBGROUP`
- `IN_GROUP`
- `HAS_GROUP`
