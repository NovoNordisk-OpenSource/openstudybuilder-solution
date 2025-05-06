# Release: January 2023


## 1. CT Config Values (Study Fields)
-------------------------------------  
### Change Description
- Values of all `study_field_*` properties on `CTConfigValue` nodes converted to snake_case.
  - [Related PR](https://orgremoved.visualstudio.com/Clinical-MDR/_git/studybuilder-import/pullrequest/69876?_a=files)
  - [Related PR](https://orgremoved.visualstudio.com/Clinical-MDR/_git/studybuilder-import/pullrequest/64722?_a=files)
  - [Related PR](https://orgremoved.visualstudio.com/Clinical-MDR/_git/clinical-mdr-api/pullrequest/65014?_a=files&path=/clinical_mdr_api/domain/study_definition_aggregate/registry_identifiers.py)
- Added `is_dictionary_term` field and removed `study_field_name_property` properties on `CTConfigValue` nodes.
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/64239?_a=files&path=/clinical_mdr_api/domain_repositories/models/configuration.py)
- Changed the values for the `configured_codelist_uid` and `configured_term_uid` properties on `CTConfigValue` nodes.
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/studybuilder-import/pullrequest/64722?_a=files&path=/datafiles/configuration/study_fields_configuration.csv)
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/studybuilder-import/pullrequest/67613?_a=files&path=/datafiles/configuration/study_fields_configuration.csv)

### Nodes Affected
- CTConfigValue


## 2. Study Selections
-------------------------------------
### Change Description
- Added `key_criteria` boolean property on `StudyCriteria` node
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/62868?_a=files&path=/clinical_mdr_api/domain_repositories/models/study_selections.py)
- Connected StudyFields to the CTTermRoot and DictionaryTermRoot nodes specified by the CT Configuration nodes
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/clinical-mdr-api/pullrequest/64239?_a=files&path=/clinical_mdr_api/domain_repositories/study_definition/study_definition_repository_impl.py)

### Nodes Affected
- StudyCriteria
- StudyField


## 3. Activites
-------------------------------------
### Change Description
Removed unnecessary `IN_SUB_GROUP`/`IN_GROUP` outgoing relations from ActivityValue/ActivitySubGroupValue nodes:
- `(n:ActivityValue)-[r:IN_SUB_GROUP]->(m:ActivitySubGroupValue)`
- `(n:ActivitySubGroupValue)-[r:IN_GROUP]->(m:ActivityGroupValue)`

Multiple outgoing relations of these types are no longer allowed, so only one of these outgoing relations will be left on each node.
### Nodes Affected
- IN_SUB_GROUP and IN_GROUP relationships removed


## 4. TemplateParameter nodes
-------------------------------------
### Change Description
- Added `TemplateParameter {name: "StudyEndpoint"}` node
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/neo4j-mdr-db/pullrequest/59375?_a=files)

### Nodes Affected
- TemplateParameter


## 5. Unit Definition nodes
-------------------------------------
### Change Description
- Added `CTTerm` related nodes for the `Study Preferred Time Unit`
- Connected `day` and `week` Unit Definitions to the created `Study Preferred Time Unit` CTTerm
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/studybuilder-import/pullrequest/72728)

### Nodes Affected
- UnitDefinition and CTTerms


## 6. Characters in CDISC term UIDs
-------------------------------------
### Change Description

- Replace all reserved characters in UIDs of `CTTermRoot` nodes, using the same logic as during CDISC data import.
  - Reserved characters: `/ &*+^=<>()[]{}%?';:$#!@,`
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/mdr-standards-import/pullrequest/74939)

### Nodes Affected
- CTTermRoot nodes for terms in CDISC library


## 7. Add "Requested" library
-------------------------------------
### Change Description
- Create the `Requested` library
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/studybuilder-import/pullrequest/72728)

### Nodes Affected
- Library (adds a single node, no relationships)


## 8. Null Flavor codelist
-------------------------------------
### Change Description
- Update `Not Applicable` to link to the current term with submission value `NA` instead of the obsolete `NOT APPLICABLE`.
- Remove link between `Null Flavor` codelist and term `Questionnaire Domain` that was created due to conflicting submission value `QS`.
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/studybuilder-import/pullrequest/72435)

### Nodes Affected
- HAS_TERM relationships from CTCodelistRoot (with codelist name `Null Flavor`)
- HAS_REASON_FOR_NULL_VALUE relationships to CTTermRoot (moved from term with submission value `NOT APPLICABLE` to `NA`)


## 9. Indexes and Constraints
-------------------------------------
### Change Description
- Re-create all db indexes and constraints according to [db schema definition](https://orgremoved.visualstudio.com/Clinical-MDR/_git/neo4j-mdr-db?path=/db_schema.py&version=GBmain&_a=contents)

### Nodes Affected
- No existing nodes or relationship are changed, but all indexes and contraints are dropped and re-created


## 10. Sponsor codelists must be extensible
-------------------------------------
### Change Description
- All sponsor codelists must be extensible, otherwise it is not possible to add their terms.
- Done by setting property `extensible=true` on their CTCodelistAttributesValue nodes.
  - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/studybuilder-import/pullrequest/69674)

### Nodes Affected
- CTCodelistAttributesValue for codelists in Sponsor library

