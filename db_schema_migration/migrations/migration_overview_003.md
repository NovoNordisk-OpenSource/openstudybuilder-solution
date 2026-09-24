# Release: post-June 2023


## 1. Indexes and Constraints
-------------------------------------
### Change Description
- Re-create all db indexes and constraints according to [db schema definition](../../db/db_schema.py).


## 2. CT Config Values (Study Fields Configuration)
-------------------------------------  
### Change Description
- Re-create all `CTConfigValue` nodes according to values defined in [this file](../../import_sponsor_data/datafiles/configuration/study_fields_configuration.csv).

### Nodes Affected
- CTConfigValue


## 3. Refactor StudySelection Labels
-------------------------------------  
### Change Description
- Migrated StudySelection node labels.
- Removed old OrderedStudySelection labels from StudyEpoch and StudyDiseaseMilestone like 
  - :OrderedStudySelection:StudyEpoch:StudySelection:
- Add StudySelection label in StudyDesignCell, StudyActivitySchedule, and StudyActivityInstruction like  
  - :StudySelection:StudyDesignCell:

- Related PR (commit `6f9783e609a2`).

### Nodes Affected
  - `StudyEpoch`
  - `StudyDiseaseMilestone`
  - `StudyDesignCell`
  - `StudyActivitySchedule`
  - `StudyActivityInstruction`

## 3. Refactor StudySelection Deletion
-------------------------------------  
### Change Description
- Migrate StudySelection Deletion
- If a StudySelection Deletion is not leaving a Last Delete node, then the last delete node is added and the StudyAction:Delete is refactored 
- The Migration will let the Deleted StudySelections remained disconnected from StudyValue node if it's not the case


- Related PR (commit `df4768936bed`).

### Nodes Affected
  - `StudySelection`

## 4. Refactor StudySelection Dropped, switched relationships and Cascade delete for StudyActivitySchedule
-------------------------------------  
### Change Description
- Migrate from StudySelection Dropped required relationships to Maintained realationships
- Migrate from StudySelection Switched required relationships to Maintained realationships
- Migrate from StudySelection:StudyActivitySchedule Cascade Delete from StudyVisit if there's still a required relationship connected to a Deleted StudySelection:StudyVisit

- Related PR (commit `df4768936bed`).

### Nodes Affected
  - `StudySelection`

## 5. ActivityGroupings
-------------------------------------  
### Change Description
- Migrate ActivityValidGroup nodes that are responsible for ActivitySubGroup and ActivityGroup combinations
- Migrate ActivityGrouping nodes that are responsible for Activity, ActivitySubGroup and ActivityGroup combinations

- Related PR (commit `3854584c7c32`).

### Nodes Affected
  - `ActivityInstanceValue`, `ActivityValue`, `ActivitySubGroupValue`, `ActivityGroupValue`

## 6. Remove T of Template from all syntax sequence_id
-------------------------------------  
### Change Description
- Removed T of Template from sequence_id of SyntaxTemplateRoot
- Removed T of Template from sequence_id of SyntaxPreInstanceRoot
- Made sequence_id of CriteriaTemplate sequential within the criteria template type
- Made sequence_id of CriteriaPreInstance sequential within the parent template

- Related PR (commit `67498242b963`).
- Related PR (commit `699f7f76c66a`).

### Nodes Affected
  - `SyntaxTemplateRoot`
  - `SyntaxPreInstanceRoot`

## 7. StudyActivitySubgroup and StudyActivityGroup selections
-------------------------------------  
### Change Description
- Migrate StudyActivitySubGroup and StudyActivityGroup selections for each StudyActivity

- Related PR (commit `c837c3dfe97d`).

### Nodes Affected
  - `StudyActivity`, `StudyActivitySubGroup`, `StudyActivityGroup`

## 8. SimpleConceptValue to be linked to a single StudyConceptRoot node
-------------------------------------  
### Change Description
- Migrate SimpleConceptValue node to be linked only to one SimpleConceptRoot and not many of them as it is at the moment.

- Related PR (commit `e8fafe5754a1`).

### Nodes Affected
  - `SimpleConceptRoot`, `SimpleConceptValue`