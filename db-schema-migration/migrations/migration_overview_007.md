# Release: post-August 2024

## Common migrations

### 1. Indexes and Constraints
-------------------------------------
#### Change Description
- Re-create all db indexes and constraints according to [db schema definition](https://orgremoved.visualstudio.com/Clinical-MDR/_git/neo4j-mdr-db?path=/db_schema.py&version=GBmain&_a=contents).


### 2. CT Config Values (Study Fields Configuration)
-------------------------------------  
#### Change Description
- Re-create all `CTConfigValue` nodes according to values defined in [this file](https://orgremoved.visualstudio.com/Clinical-MDR/_git/studybuilder-import?path=/datafiles/configuration/study_fields_configuration.csv).

#### Nodes Affected
- CTConfigValue


## Relese specific migrations
This release contains no changes to the data model.
No release specific migrations are required.


