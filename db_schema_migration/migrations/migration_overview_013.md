# Release: 1.14.0 (post-June 2025)

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


### 3. Migrate `consecutive_visit_group` property of :StudyVisit node into separate :StudyVisitGroup node
#### Change Description
- Refactored `consecutive_visit_group` property into separate :StudyVisitGroup node to support different grouping techniques.

#### Nodes Affected
- `StudyVisit`

#### Relationships affected
- `IN_VISIT_GROUP`