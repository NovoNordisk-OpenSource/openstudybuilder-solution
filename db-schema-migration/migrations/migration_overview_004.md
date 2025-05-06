# Release: post-June 2023


## 1. Indexes and Constraints
-------------------------------------
### Change Description
- Re-create all db indexes and constraints according to [db schema definition](https://orgremoved.visualstudio.com/Clinical-MDR/_git/neo4j-mdr-db?path=/db_schema.py&version=GBmain&_a=contents).


## 2. CT Config Values (Study Fields Configuration)
-------------------------------------  
### Change Description
- Re-create all `CTConfigValue` nodes according to values defined in [this file](https://orgremoved.visualstudio.com/Clinical-MDR/_git/studybuilder-import?path=/datafiles/configuration/study_fields_configuration.csv).

### Nodes Affected
- CTConfigValue


## 3. Merge ActivityItemRoot&Value node pairs to single ActivityItem node
-------------------------------------  
### Change Description
- Convert each ActivityItemRoot and ActivityItemValue node pair to ActivityItem nodes that are versioned via the ActivityInstanceValue node.
  The root/value pairs can be shared by several instances, while the new nodes belong to their instance.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/102208).

### Nodes Affected
  - `ActivityItemRoot`
  - `ActivityItemValue`
  - `ActivityItem`

## 4. Merge ActivityItem nodes of same class to a single node for each ActivityInstance
-------------------------------------  
### Change Description
- Merge separate nodes belonging to the same ActivityItemClass that are connected to each ActivityInstance.
  After merging, each ActivityItem node may have relatiohsips to several ct terms or unit definitions. 

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/104659).

### Nodes Affected
  - `ActivityItem`


## 5. StudyActivitySubgroup and StudyActivityGroup selections
-------------------------------------  
### Change Description
- Migrate StudyActivitySubGroup and StudyActivityGroup selections for each StudyActivity

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/100824).


## 6. StudySoAGroup selection
-------------------------------------  
### Change Description
- Migrate StudySoAGroup node for each StudyActivity. Reconnect HAS_FLOWCHART_GROUP relationship that points
- to CTTermRoot from StudyActivity into StudySoAGroup.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/103484).

### Nodes Affected
  - `StudyActivity`
  - `StudySoAGroup`


## 7. Removal of Study relationships for StudyActivitySubGroup, StudyActivityGroup and StudySoAGroup
-------------------------------------  
### Change Description
- Remove Study relationships for `StudyActivitySubGroup`, `StudyActivityGroup` and `StudySoAGroup`
- Migrate relationship between StudyActivity and StudyActivityGroup called `STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP`.
- Remove relationship between StudyActivitySubGroup and StudyActivityGroup called `STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP`
- Add new label for `StudyActivitySubGroup`, `StudyActivityGroup` and `StudySoAGroup` nodes called `StudySelectionMetadata` and remove `StudySelection` label
- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/105127).

### Nodes Affected
  - `StudyActivity`
  - `StudySoAGroup`
  - `StudyActivitySubGroup`
  - `StudyActivityGroup`
  - `StudyValue`
  - `StudySelectionMetadata`


## 8. Refinement of `sequence_id`s of all `SyntaxTemplateRoot`s and `SyntaxPreInstanceRoot`s
-------------------------------------  
### Change Description
- Renumbered `sequence_id`s of all `SyntaxTemplateRoot`s and `SyntaxPreInstanceRoot`s
- Prefixed all `sequence_id`s of `SyntaxTemplateRoot`s in User Defined library with `U-`
- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/108796).

### Nodes Affected
  - `SyntaxTemplateRoot`
  - `SyntaxPreInstanceRoot`


