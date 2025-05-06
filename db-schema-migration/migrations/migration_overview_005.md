# Release: post-October 2023


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


## 3. Fix StudyEpoch order as only StudyEpochs from same Subtype were reordered
-------------------------------------  
### Change Description
- There was a bug that only StudyEpochs from the same Subtype were reordered when some StudyEpoch got deleted/modified or reordered.
- Actually all StudyEpochs placed after the StudyEpoch that got changed should be reordered.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/110142).

### Nodes Affected
  - `StudyEpoch`


## 4. Link DatasetVariables with CT Terms based on their Value List
-------------------------------------------------------------------
### Change Description
- We added a new step in the data model part of the mdr-standards import : when DatasetVariables have a value_list property, we want to create a relationship to the CTTerms holding each of the values in this list
- The script goes through several steps to guess which CTTerm to link to ; in the end, all DatasetVariables should be linked with exactly as many CTTermRoot nodes as there are values in its Value List.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/mdr-standards-import/pullrequest/110315)

### Relationships Created
  - `(:DatasetVariableInstance)-[:REFERENCES_TERM]->(:CTTermRoot)`


## 5. Refactor StudyField Deletion
-------------------------------------  
### Change Description
- Migrate StudyField Deletion
- If a StudyField Deletion is not leaving a Last Delete node, then the last delete node is added and the StudyAction:Delete is refactored 
- The Migration will let the Deleted StudyFields remained disconnected from StudyValue node if it's not the case

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/db-schema-migration/pullrequest/109564).

### Nodes Affected
  - `StudyField`


## 6. Add missing LATEST_nnnn relationships
-------------------------------------
### Change Description
- Some versioned items are missing the LATEST_DRAFT, LATEST_RETIRED or LATEST_FINAL shortcuts.
- This migration adds the missing relationships, to ensure that the latest version for each status
  has a corresponding LATEST_nnnn relationship.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/114648).

### Relationships Created
  - `(:nnnRoot)-[:LATEST_DRAFT]->(:nnnValue)`
  - `(:nnnRoot)-[:LATEST_RETIRED]->(:nnnValue)`
  - `(:nnnRoot)-[:LATEST_FINAL]->(:nnnValue)`


## 7. Merge StudyAction node linked to the StudyActivityGroup to a proper StudyRoot node
-------------------------------------  
### Change Description
- There was a bug introduced in the migration 003 that the StudyActivityGroup's StudyAction node was linking into blank
- StudyRoot node instead of the real StudyRoot node.

### Nodes Affected
  - `StudyRoot`
  - `StudyAction`
  - `StudyActivityGroup`


## 8. Migrate StudyActivityInstances nodes that should be created implicitly when StudyActivity is created
-------------------------------------  
### Change Description
- Removes incorrectly migrated StudyActivityInstances as these are not used in production database
  yet and will be recreated by following steps.
- The StudyActivityInstance nodes should be created when the StudyActivity is being created.
- The created StudyActivityInstance should link to the ActivityInstance node in case if the selected Activity
- for the StudyActivity is linked by some ActivityInstance

### Nodes Affected
  - `StudyActivityInstance`
  - `StudyActivity`
  - `ActivityInstanceValue`

removes incorrectly migrated StudyActivityInstances as these are not used in production database yet and will be recreated by next migration step

## 9. Remove duplicated StudyActivitySchedule nodes that link to same StudyActivity and StudyVisit
-------------------------------------  
### Change Description
- The duplicated StudyActivitySchedule nodes were created because of the missing API check.
- We allowed to created StudyActivitySchedule that link to the same StudyActivity and StudyVisit.

### Nodes Affected
  - `StudyActivitySchedule`
  - `StudyActivity`
  - `StudyVisit`


## 10. Add WeekInStudy relationships for StudyVisit
-------------------------------------  
### Change Description
- Added `WeekInStudyRoot` node and `WeekInStudyValue` node
- Added `TemplateParameter` node with property `name`="`WeekInStudy`"
- Added `WeekInStudy` relationship between `StudyVisit` and `WeekInStudyRoot`

### Nodes Affected
  - `WeekInStudyRoot`
  - `WeekInStudyValue`
  - `TemplateParameter`
  - `StudyVisit`


## 11. Add soa_preferred_time_unit StudyTimeField
-------------------------------------  
### Change Description
- Added `StudyTimeField` node with `name`="`soa_preferred_time_unit`"

### Nodes Affected
  - `StudyRoot`
  - `StudyValue`
  - `StudyTimeField`
  - `StudyAction`
  - `UnitDefinitionRoot`


## 12. Merge duplicated nodes around StudyActivity Groups and Subgroups
### Change Description
- Correct duplicated `StudyActivityGroup` and `StudyActivitySubGroup` nodes specific to study uid `Study_000002`
- Merge duplicated `StudyActivitySubGroup` nodes connecting a `StudyActivity` node to a `ActivitySubGroupValue` node
- Merge duplicated `StudyActivityGroup` nodes connecting a `StudyActivity` node to a `ActivityGroupValue` node
- Remove incomplete `Edit` `StudyAction` nodes for `StudyActivitySubGroup`s, where the `Edit` lacks an `AFTER`
- Remove incomplete `Edit` `StudyAction` nodes for `StudyActivityGroup`s, where the `Edit` lacks an `AFTER`
- Add missing `Create` `StudyAction` nodes for `StudyActivityGroup` and `StudyActivitySubGroup` nodes

### Nodes Affected
  - `StudyActivitySubGroup`
  - `StudyActivityGroup`
  - `Edit`
  - `Create`


## 13. Nullify UnitDefinitionValue.name_sentence_case & update SyntaxInstanceValue.name and SyntaxInstanceValue.value
### Change Description
- 

### Nodes Affected
  - `UnitDefinitionValue`
  - `SyntaxInstanceRoot`
  - `SyntaxInstanceValue`


## 14. Add missing ActivityItemClass for ActivityItems
### Change descriptiom
- Adds a relationship to an `ActivityItemClassRoot` for `ActivityItem` nodes that are missing this.
  There are 9 such nodes in production.
- All affected nodes should be linked to the `test_name_code` item class.

### Relationships Created
  - `(:ActivityItemClassRoot)-[:HAS_ACTIVITY_ITEM]->(:ActivityItem)`


## 15. Remove wrongly created Activity Instances that lack Activity
### Change descriptiom
- Finds `ActivityInstanceValue` nodes that lack a `HAS_ACTIVITY` relationship.
- Remove these instance values, with their root node, and any associated activity items.

### Nodes Affected
  - `ActivityInstanceRoot`
  - `ActivityInstanceValue`
  - `ActivityItem`

