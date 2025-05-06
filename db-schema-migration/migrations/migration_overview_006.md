# Release: post-March 2024


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


## 3. Migrate StudyActivityInstances nodes that should be created implicitly when StudyActivity is created
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


## 4. Rename 'INSERTION_VISIT' visit_class propert into 'MANUALLY_DEFINED_VISIT'
-------------------------------------  
### Change Description
- Update those StudyVisit nodes that have `INSERTION_VISIT` set as visit_class property. The value should be updated
- to `MANUALLY_DEFINED_VISIT`.

### Nodes Affected
  - `StudyVisit`


## 5. Fix StudyDurationDays, StudyDurationWeeks, WeekInStudy properties for StudyVisits with negative timings
-------------------------------------  
### Change Description
- The `StudyDurationDays`, `StudyDurationWeeks` and `WeekInStudy` properties were incorrectly calculated for Studies with negative timings.
- The following migration fixes those values to be equal to StudyDay and StudyWeek values for the negative values.

### Nodes Affected
- `StudyVisit`
- `StudyDurationDays`
- `StudyDurationWeeks`
- `WeekInStudy`


## 6. Fix StudyWeek property for StudyVisits that have timing greater than -7 and less than 0.
-------------------------------------  
### Change Description
- The `StudyWeek` was incorrectly calculcated for the StudyVisits from the -7 < timing < 0 days interval.
- It should be set to -1 for such timing values.

### Nodes Affected
- `StudyWeek`


## 7. Merge StudyActivitySubGroup, StudyActivityGroup and StudySoAGroup nodes to be reused if possible
-------------------------------------  
### Change Description
- If a StudyActivity is using the same ActivitySubGroup, ActivityGroup or SoAGroup, theirs corresponding StudyMetadataSelections
- should be reused between different StudyActivities

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/107866).

### Nodes Affected
  - `StudyActivity`
  - `StudyActivitySubGroup`
  - `StudyActivityGroup`
  - `StudySoAGroup`


## 8. Remove unwanted extra STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP/STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP relationships
-------------------------------------  
### Change Description
- At some point, an API bug caused to create StudyActivities for all possible groupings of the Activity selected by the user.
- For instance if 'Albumin' Activity has 3 possible groupings, we were creating StudyActivity for each specific grouping.
- The correct behaviour should be, to create only one StudyActivity for the grouping that was selected by the user during the StudyActivity creation time.

### Nodes Affected
  - `StudyActivity`
  - `StudyActivitySubGroup`
  - `StudyActivityGroup`

### Relationships Affected
  - `STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP`
  - `STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP`


## 9. Correct SoAGroup information represented in the old format.

### Change Description
- At some point we decided to change schema of SoAGroup representation within StudyActivity nodes.
- Previous representation was (:StudyActivity)-[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)
- The current representation should be (:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)
- This schema change was implemented in the migration_004 but the list of StudyActivity nodes to be migrated was only containining these StudyActivity ndoes 
- that were at that time linked to StudyValue. It means that we only updated last versions of given StudyActivities nodes and past versions were untouched.
- The correction is separated into 2 parts.
- Part one reuses already existing StudySoAGroup nodes if the latest version of a specific StudyActivity is using the same soa_group CTTermRoot node.
- Part two creates new StudySoAGroup node if the latest version of a specific StudyActivity is using the different soa_group CTTermRoot node.
### Nodes Affected
  - `StudyActivity`
  - `StudySoAGroup`
  - `StudyActivityGroup`

### Relationships Affected
  - `STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP`
  - `HAS_FLOWCHART_GROUP`


