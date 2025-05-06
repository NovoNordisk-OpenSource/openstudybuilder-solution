# Release: post-June 2024


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


## 3. Fix issue of wrongly edited SoAGroups
-------------------------------------  
### Change Description
- There was an issue related to the functionality introduced in the release 1.6.
- The functionality is about reusing StudySoAGroup, StudyActivityGroup or StudyActivitySubGroup between different StudyActivities if possible.
- It is possible to reuse such nodes when StudyActivities are in the same Study and they share chosen SoAGroup, ActivityGroup or ActivitySubGroup.
- The issue was that when editing a SoAGroup of a given StudyActivity, the StudyActivity wasn't reassigned with a new SoAGroup but the old (shared) SoAGroup node was patched.
- That caused the other StudyActivities that were referencing same SoAGroup (before it was edited) to reference the old-outdated version of the SoAGroup.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/151426).
- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/152425).

### Nodes Affected
  - `StudyActivity`
  - `StudySoAGroup`


## 4. Merge StudyActivitySubGroup, StudyActivityGroup and StudySoAGroup nodes to be reused if possible
-------------------------------------  
### Change Description
- Because of the issue described in the point (3) some of the SoAGroup nodes, StudyActivityGroups, StudyActivitySubGroups were created in the not shared way,
- meaning that we have for instance two StudySoAGroup nodes in scope of a single Study for the `Efficacy` term.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/107866).

### Nodes Affected
  - `StudyActivity`
  - `StudyActivitySubGroup`
  - `StudyActivityGroup`
  - `StudySoAGroup`


## 5. Submit all ActivityRequests and reject those unwanted
-------------------------------------------------------------------
### Change Description
- We added a new steps in the data ActivityRequests flow. We have added submit and rejection step.
- All existing ActivityRequests should be marked as submitted.
- We should reject those ActivityReuests that are in the `Retired` state and don't have Sponsor Activity created out of them.

### Nodes Affected
  - `ActivityValue`

### Properties Set
  - `is_request_final`
  - `is_request_rejected`


## 6. Migrate StudyActivities linked to deleted SoAGroup
-------------------------------------------------------------------
### Change Description
- Because of the API issue mentioned in the Related PR, some of the StudyActivities were linking to the Deleted StudySoAGroup node.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/152581).

### Nodes Affected
  - `StudyActivity`
  - `StudySoAGroup`


## 7. Remove SoAGroup nodes not linked to any StudyActivites
-------------------------------------------------------------------
### Change Description
- Some of the StudySoAGroup nodes were not Deleted and attached to any StudyActivites.
- That shouldn't be possible, an active StudySoAGroup should be linked to some StudyActivity

### Nodes Affected
  - `StudyActivity`
  - `StudySoAGroup`


