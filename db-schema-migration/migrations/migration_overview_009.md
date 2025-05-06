# Release: post-October 2024

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


## Release specific migrations

### 1. Refactoring StudySelectionMetadata nodes to StudySelection
-------------------------------------  
#### Change Description
- Changing the StudySelectionMetadata node labels into StudySelection.
- Linking refactored StudySelection nodes to StudyValue node.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/166631).

#### Nodes Affected
- `:StudySelectionMetadata`



