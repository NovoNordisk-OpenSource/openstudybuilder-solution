# Release: post-February 2023


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


## 3. Refactoring of Syntax Templates & Instances
-------------------------------------
### Change Description
- Added `SyntaxInstanceRoot` label to:
  - `ActivityInstructionRoot`
  - `CriteriaRoot`
  - `EndpointRoot`
  - `ObjectiveRoot`
  - `TimeframeRoot`
- Added `SyntaxInstanceValue` label to:
  - `ActivityInstructionValue`
  - `CriteriaValue`
  - `EndpointValue`
  - `ObjectiveValue`
  - `TimeframeValue`
- Added `SyntaxIndexingInstanceRoot` label to:
  - `CriteriaRoot`
  - `EndpointRoot`
  - `ObjectiveRoot`
- Added `SyntaxIndexingInstanceValue` label to:
  - `CriteriaValue`
  - `EndpointValue`
  - `ObjectiveValue`
- Added `SyntaxTemplateRoot` label to:
  - `ActivityDescriptionTemplateRoot`
  - `CriteriaTemplateRoot`
  - `EndpointTemplateRoot`
  - `ObjectiveTemplateRoot`
  - `TimeframeTemplateRoot`
- Added `SyntaxTemplateValue` label to:
  - `ActivityDescriptionTemplateValue`
  - `CriteriaTemplateValue`
  - `EndpointTemplateValue`
  - `ObjectiveTemplateValue`
  - `TimeframeTemplateValue`
- Added `SyntaxIndexingTemplateRoot` label to:
  - `CriteriaTemplateRoot`
  - `EndpointTemplateRoot`
  - `ObjectiveTemplateRoot`
- Added `SyntaxIndexingTemplateValue` label to:
  - `CriteriaTemplateValue`
  - `EndpointTemplateValue`
  - `ObjectiveTemplateValue`
- Renamed `TemplateParameterValueRoot` label to `TemplateParameterTermRoot`
- Renamed `TemplateParameterValue` label to `TemplateParameterTermValue`
- Renamed `ActivityDescriptionTemplateRoot` label to `ActivityInstructionTemplateRoot`
- Renamed `ActivityDescriptionTemplateValue` label to `ActivityInstructionTemplateValue`
- Renamed `HAS_VALUE` relationship of `TemplateParameter` to `HAS_PARAMETER_TERM`
- Renamed `HAS_SUB_CATEGORY` relationship to `HAS_SUBCATEGORY`
- Renamed `HAS_DISEASE_DISORDER` relationship to `HAS_INDICATION`
- Renamed `OV_USES_VALUE`, `EV_USES_VALUE`, `TV_USES_VALUE`, `CT_USES_VALUE` and `AT_USES_VALUE` relationships to `USES_VALUE`
- Renamed `OT_USES_PARAMETER`, `ET_USES_PARAMETER`, `TT_USES_PARAMETER`, `CT_USES_PARAMETER` and `AT_USES_PARAMETER` relationships to `USES_PARAMETER`

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/77924https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/77924)


## 4. Default study preferred time unit
-------------------------------------  
### Change Description
- Added `StudyField:StudyTimeField` node connected to latest `StudyValue` node for each Study.
- Created `StudyField` node links to `UnitDefinitionRoot` node by `HAS_UNIT_DEFINITION` relationship.
- Added `StudyField` describes the default study preferred time unit that is currently instantiated on Study creation.
- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/76653).

### Nodes Affected
- StudyValue, StudyField, UnitDefinitionRoot


## 5. Item versioning
-------------------------------------  
### Change Description
- Add missing `HAS_VERSION` for all `LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED` relationships.
- Remove duplicated `HAS_VERSION` relationships.
- Remove any properties from `LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED` relationships.
- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/79961).

### Nodes Affected
- None, only affects relationships
### Relationships Affected
- HAS_VERSION, LATEST_DRAFT, LATEST_FINAL and LATEST_RETIRED that do not start from a node with label 
  ClassVariableRoot, DatasetClassRoot, DatasetRoot, DatasetScenarioRoot, DatasetVariableRoot or StudyRoot

## 6. Syntax Sequence ID
-------------------------------------  
### Change Description
- Add a new property `sequence_id` to all Syntax Template Root nodes.
- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/79961).

### Nodes Affected
  - `ActivityInstructionRoot`
  - `CriteriaTemplateRoot`
  - `EndpointTemplateRoot`
  - `ObjectiveTemplateRoot`
  - `TimeframeTemplateRoot`

## 7. Activity Instance Class
-------------------------------------  
### Change Description
- Migrated ActivityInstanceClass nodes using the migration methods from data_import repository.
- Link ActivityInstanceValue with the migrated ActivityInstanceClassRoot node.
- Removed old ActivityInstanceRoot labels like 
  - :EventRoot:FindingRoot:CategoricFindingRoot:NumericFindingRoot:TextualFindingRoot
- Removed old ActivityInstanceValue labels like 
  - :EventValue:FindingValue:CategoricFindingValue:NumericFindingValue:TextualFindingValue
- Removed extra relationships to ActivityDefinition node that was responsible for pointing other nodes like Specimen or SDTM_DOMAIN.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/82515).

### Nodes Affected
  - `ActivityInstanceClassRoot`
  - `ActivityInstanceClassValue`
  - `ActivityInstanceRoot`
  - `ActivityInstanceValue`
  - `ActivityDefinition`

## 8. ActivityItemClass relationship to Role and Data type
-------------------------------------  
### Change Description
- Migrated relationship that represents an ActivityItemClass Role to the "NA" CTTerm.
- Migrated relationship that represents an ActivityItemClass Data type to the "NA" CTTerm.
- This migration is performed to make ActivityItemClasses functional after making Role and Data type properties required.
- Just after this migration, the data import script should be run to patch ActivityItemClasses with real CTTerm values.

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/89388).

### Nodes Affected
  - `ActivityItemClassValue`
  - `CTTermRoot`

## 9. ActivityInstanceValue dummy relationship to ActivityValue when missing
-------------------------------------
### Change Description
- Add a dummy IN_HIERARCHY relationship from ActivityInstanceValues to ActivityValue with name "Technical Complaint" when missing.
- This migration is performed to make the few activity instances that lack a relationship to an activity functional.
- Just after this migration, the data import script should be run to patch ActivityInstanceValues with real ActivityValues.

### Nodes Affected
  - `ActivityValue`
  - `ActivityInstanceValue`

## 9. OdmTemplateRoot & OdmTemplateValue renamed to OdmStudyEventRoot & StudyEventValue
-------------------------------------
### Change Description
- `OdmTemplateRoot` & `OdmTemplateValue` renamed to `OdmStudyEventRoot` & `StudyEventValue`.
- `display_in_tree` property added to value node.

### Nodes Affected
  - `OdmTemplateRoot`
  - `OdmTemplateValue`

- [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/91497).


