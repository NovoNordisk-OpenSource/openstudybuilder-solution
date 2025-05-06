# Release: 1.11.0 (post-December 2024)

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


### 3. Changed the value of `name` property of Activity Instance Class and added `level`
#### Change Description
- Changed the value of the `name` property
- Added a new `level` property

#### Nodes Affected
- `ActivityInstanceClassValue`


### 4. Reconnected all Activity Instance Classes `PARENT_CLASS` relationship
#### Change Description
- Reconnected all Activity Instance Classes `PARENT_CLASS` relationship in accordance with the `activity_instance_class.csv`

#### Nodes Affected
- `ActivityInstanceClassRoot`


### 5. Removed old nodes and moved their relationships to new nodes
#### Change Description
- Removed `AssociatedPersonsFinding`, `Other` and `OtherQualifiers` nodes
- Moved relationships (no such relationship exist) from old `DeviceFinding` and `DeviceNumericFinding` nodes to `NumericFindings` node and delete the old ones
- Moved relationships from old `CompoundDosing` and `ConcomitantMedication` nodes to `Interventions` node and delete the old ones
- Moved relationships from old `AdverseEvent`, `MedicalHistory`, `Disposition`, `HypoglycaemicEpisode` nodes to `Events` node and delete the old ones

#### Nodes Affected
- `ActivityInstanceRoot`
- `ActivityInstanceValue`
- `ActivityInstanceClassRoot`
- `ActivityInstanceClassValue`
- `ActivityItemClassRoot`
- `ActivityItemClassValue`


### 6. Updated `is_adam_param_specific` property of Activity Item to False if it is NULL
#### Change Description
- Updated `is_adam_param_specific` property of Activity Item to False if it is NULL

#### Nodes Affected
- `ActivityItem`


### 7. Moved and added specific properties from Activity Item Class Value node to relationship
#### Change Description
- Moved `mandatory` property from Activity Item Class Value node to relationship `HAS_ITEM_CLASS` between `ActivityItemClassRoot` and `ActivityInstanceClassRoot`
- Added `is_adam_param_specific_enabled` property to relationship `HAS_ITEM_CLASS` between `ActivityItemClassRoot` and `ActivityInstanceClassRoot`

#### Nodes Affected
- `ActivityItemClassValue`

#### Edges Affected
- `HAS_ITEM_CLASS`


### 8. Loading relationships between Dataset Domains and Activity Instance Classes
-------------------------------------  
#### Change Description
- Added new `HAS_DATA_DOMAIN` relationship from Activity Instance Classes to Dataset Domains

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/205344).

#### Nodes Affected
- `:CTTermRoot`
- `:ActivityInstanceClassRoot`


### 9. Loading relationships between Activity Item Classes and Codelists
-------------------------------------  
#### Change Description
- Added new `RELATED_CODELIST` relationship from Activity Item Class to Codelist

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/207352).

#### Nodes Affected
- `:CTCodelistRoot`
- `:ActivityItemClassRoot`


### 10. Protocol SoA snapshot
----------------------------  
#### Change Description
- Assign the order property for StudySoAGroup, StudyActivityGroup, StudyActivtySubGroup and StudyActivity based on their order in DetailedSoA.
- The new order property describes order of given items in scope of their parent grouping.
  [PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/208978)

#### Nodes affected
- StudyActivity
- StudySoAGroup
- StudyActivityGroup
- StudyActivitySubGroup
#### Relationships affected
- STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP
- STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP
- STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP


