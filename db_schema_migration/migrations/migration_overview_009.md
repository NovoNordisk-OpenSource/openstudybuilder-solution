# Release: post-October 2024

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

### 1. Refactoring StudySelectionMetadata nodes to StudySelection
-------------------------------------  
#### Change Description
- Changing the StudySelectionMetadata node labels into StudySelection.
- Linking refactored StudySelection nodes to StudyValue node.

- Related PR (commit `efe45b9658b7`).

#### Nodes Affected
- `:StudySelectionMetadata`

