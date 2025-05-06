---
title: Control Terminology Data Model
date: 2021-08-06
---

# Control Terminology Model
At its core, Control Terminology provides a standardized set of values required for generating CDISC-compliant datasets. 
In our model, Control Terminology can also be extended with Sponsor defined values - in particular, Novo Nordisk specific naming for certain values.

The two main building blocks of control terminology are:
- **Terms**: standardized names for terminology used in a clinical context. E.g. "100mg/L", "Weight", "Intravenously".
- **Codelists**: groupings of terms that fit into the same category. E.g. "Dose Unit", "Dimension", or "Route of Administration".

Control Terminology items can be selected as part of library objects, like objectives and endpoints, but also dictionaries, assessments and other concepts.

A snapshot of the part of the data model concerning control terminology is shown below.

![Data Model Documentation](~@source/images/model/physical_data_model/control-terminology.png)

_The above image is a snapshot of the model as of July 16th, 2021._

## Terminology
The following terminology is used for the control terminology as stored in the graph.

| Concept          | Description                                                                                                                                                                                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| Catalogue       | A control terminology catalogue containing a collection of codelists. Each incremental load of the new codelists is grouped as a package.                                                                                                                                                                |
| Package      |   A set of codelists loaded at a given point in time.                                                                                                                                                   |
| Package Codelist      | A codelist as present in a package. This is just a reference object, linking the package to the actual codelist.                                                                                          |
| Package Term | A term as present in a package. This is just a reference object, linking the package codelist to the actual term.                                                                                                                                                                         |
| Codelist     | A group of terms of a given type. An example: `Anatomical Location`                                                                                                                                   |
| Term | A value that can be selected from a codelist. Examples: `Elbow, Hand, Leg`.                                                            |
| Codelist/Term Attributes       | Standard (CDISC) namings for control terminology codelists and terms.                           |
| Codelist/Term Name    | Sponsor-defined namings for control terminology, used in addition to the attributes. |


### Catalogues and Packages
Catalogues and packages are created by the CDISC import script on a schedule.
If the import script loads a catalogue that previously existed in the database, a new package is created.
A package therefore represents a snapshot of a CDISC release.

> The graph structure around packages (CTPackage, CTPackageCodelist, CTPackageTerm) do not hold data from the codelists/terms. These are stored seperately. The package structure simply acts as a reference tree, with links to the data nodes.

### Sponsor Defined & Non-Sponsor Control Terminology
We have split the Codelists and the Terms into two set of metadata: 
- Attribute values - metadata from the CDISC library, version controlled and grouped.
- (Sponsor-defined) name values - allowing a sponsor (e.g. Novo Nordisk) to provide a custom name for each codelist or term.

For a single codelist or term, the standard attribute values and sponsor-defined values are versioned seperately. This is also reflected in the graph.
> One CTCodelistRoot has exactly one CTCodelistAttributesRoot and one CTCodelistNameRoot. It can have multiple versions of both of these. The same applies to terms.

### Codelist Configurations
Codelist configurations are used to bind specific codelists to part of the study configuration.
For example, we might want to specify that codelist C43023 can be used to select objective types.
This configuration is versioned, and stored in the database.

There are two types of codelist configurations that are stored in the graph:
- `FieldNameConfig` - to define which codelist can be used to select a specific study field type.
- `SelectionRelTypeConfig` - to define which codelist can be used to select a specific study selection.

A seperate API endpoint is defined to create and update codelist configurations.

## Business Logic
Control terminology is created and updated either from the periodic import scripts, or from a set of API endpoints.
Terms and codelists can only be connected to other parts of the system if they are in a final released state.

## Node Labels
The following node labels are part of the control terminology model:

### CTCatalogue
- Description: A reference to a catalogue containing control terminology.
- Example: `SDTM CT`
- Properties:
  - `name: String (Required, Unique)`: An unique name (identifier) for the catalogue.
- Relationships:
  - `CONTAINS_PACKAGE (Outgoing, 0..*)`: links to each of the package releases for the catalogue. 
  - `HAS_CODELIST (Outgoing, 0..*)`: links to the latest codelists in the catalogue. 
  - `HAS_CATALOGUE (Incoming, 1)`: a link to the library that the catalogue is in.

### CTPackage
- Description: a package (snapshot) of a catalogue at a given point in time. 
- Example: `SDTM CT (06/06/2021)`
- Properties:
  - `uid: String (Required, Unique)`: unique identifier for the package.
  - `href: String`: A path/URL to where the package was loaded from.
  - `name: String`: The name of the package release (a catalogue name and a date)
  - `label: String`: type of the package (e.g. "Terminology")
  - `description: String`: a long description of the package contents.
  - `source: String`: the source of the import package.
  - `effective_date: Date`: From which date the package was used by CDISC.
  - `registration_status: String`: status of the package at CDISC.
  - `import_date: DateTime`: At what time the package was imported into the MDR.
  - `author_id: String`: User ID of the person that performed the import. 
- Relationships:
  - `CONTAINS_CODELIST (Outgoing, 0..*)`: links to the package codelists that were part of the package.
  - `CONTAINS_PACKAGE (Incoming, 1)`: a link to the catalogue this package is an instance of. 
  
### CTPackageCodelist
- Description: a snapshot of a codelist loaded in a package at a given point in time. The `CTPackageCodelist` node points to the actual `CTCodelistAttributesValue` nodes with the detailed data. 
- Example: `"SDTM CT (06/06/2021) - CTCodelist_000001"`
- Properties:
  - `uid: String`: unique identifier for the codelist as loaded as part of the package.
- Relationships:
  - `CONTAINS_TERM (Outgoing, 0..*)`: links to the loaded terms as part of the package.
  - `CONTAINS_ATTRIBUTES (Outgoing, 1)`: a link to the actual (data-holding) codelist attributes nodes. 
  - `CONTAINS_CODELIST (Incoming, 1)`: a link to the control terminology package as part of the snapshot.
  
### CTPackageTerm
- Description: a snapshot of a term loaded in a package at a given point in time. The `CTPackageTerm` node points to the actual `CTTermAttributesValue` nodes with the detailed data. 
- Example: `"SDTM CT (06/06/2021) - CTTerm_000001"`
- Properties:
  - `uid: String`: unique identifier for the term as loaded as part of the package.
  > **Note:** The `uid` is of the form: `<effective date> + '_' + <catalogue name> + '_' + <term concept id> + '_' + <term code-submission-value>`
- Relationships:
  - `CONTAINS_ATTRIBUTES (Outgoing, 1)`: a link to the actual (data-holding) term attributes nodes.
  - `CONTAINS_TERM (Incoming, 0..*)`: links to the control terminology codelist as part of the snapshot.
  
### CTCodelistRoot
- Description: The main reference for a control terminology codelist. It contains links to an attributes root (standard control terminology) and a name root (sponsor defined codelists).
- Example: `CTCodelist_000001`
- Properties:
  - `uid: String`: unique ID of the control terminology codelist.
- Relationships:
  - `HAS_ATTRIBUTES_ROOT (Outgoing, 1)`: a link to the standard control terminology object.
  - `HAS_NAME_ROOT (Outgoing, 1)`: a link to the matching sponsor-defined control terminology object.
  - `HAS_TERM (Outgoing, 0..*)`: links to the terms currently in the codelist.
  - `HAD_TERM (Outgoing, 0..*)`: links to the terms that were previously in the codelist.
  - `HAS_CONFIGURED_CODELIST (Incoming, 0..*)`: if the codelist is configured as a standard selectable codelist, a link to the configuration parameters. 
  - `CONTAINS_CODELIST (Incoming, 1)`: link to the library that the codelist is in.
  
### CTCodelistAttributesRoot
- Description: A root object for the standard control terminology codelist. It has one or more multiple versions.
- Example: (no value, this node is a pointer)
- Properties:
  - `(none)`
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the standard codelist. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the standard codelist.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the standard codelist.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the standard codelist.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the standard codelist.
  - `HAS_ATTRIBUTES_ROOT (Incoming, 1`): A pointer to the root codelist object.
 
### CTCodelistAttributesValue
- Description: A node representing an instance of a standard codelist, in a specific version.
- Example: `"CDISC SDTM Anatomical Location"`
- Properties:
  - `name: String`: name of the codelist.
  - `submission_value: String`: submission value for the codelist.
  - `preferred_term: String`: the preferred term name of the codelist.
  - `definition: String`: a textual description of the codelist definition.
  - `extensible: Boolean`: whether the codelist is extensible with custom terms.
  - `synonyms: String[]`: a list of synonym codelist names.
- Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  - `CONTAINS_ATTRIBUTES (Incoming, 1)`: A link to the CTPackageCodelist for this codelist.

### CTCodelistNameRoot
- Description: A root object for the sponsor-defined control terminology codelist. It has one more multiple versions.
- Example: (no value, this node is a pointer)
- Properties:
  - `(none)`
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the sponsor-defined codelist. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the sponsor-defined codelist.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the sponsor-defined codelist.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the sponsor-defined codelist.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the sponsor-defined codelist.
  - `HAS_NAME_ROOT (Incoming, 1`): A pointer to the root codelist object.
 
### CTCodelistNameValue
- Description: A node representing an instance of a sponsor defined codelist, in a specific version.
- Example: `Novo Nordisk Standard Anatomical Place`
- Properties:
  - `name: String`
- Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  
### CTTermRoot
- Description: The main reference for a control terminology term. It contains links to an attributes root (standard control terminology) and a name root (sponsor defined terms).
- Example: `CTTermRoot_000001`
- Properties:
  - `uid: String`: Unique ID of the term.
  > **Note:** The `uid` is of the form: `<term concept id> + '_' + <term code-submission-value>`
- Relationships:
  - `HAS_ATTRIBUTES_ROOT (Outgoing, 1)`: a link to the standard control terminology object.
  - `HAS_NAME_ROOT (Outgoing, 1)`: a link to the matching sponsor-defined control terminology object.
  - `HAS_PARENT_TYPE (Outgoing, 0..1)`: a link to a CT term designated as the term's parent type.
  - `HAS_PARENT_SUB_TYPE (Outgoing, 0..1)`: a link to a CT term designated as the term's parent sub-type.
  - `HAS_TERM (Incoming, 0..*)`: links to one or more codelists the term is currently in.
  - `HAD_TERM (Incoming, 0..*)`: links to one or more codelists the term was in.
  - **Incoming relationships from library elements that used a term are omitted here. See each individual component for details.**

### CTTermAttributesRoot
- Description: A root object for the standard control terminology term. It has one or  multiple versions.
- Example: (no value, this node is a pointer)
- Properties:
  - `(none)`
- Relationships:
- `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the standard term. 
- `LATEST (Outgoing, 1`): A pointer to the latest value of the standard term.
- `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the standard term.
- `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the standard term.
- `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the standard term.
- `HAS_ATTRIBUTES_ROOT (Incoming, 1`): A pointer to the root term object.

### CTTermAttributesValue
- Description: A node representing an instance of a standard term, in a specific version.  
- Example: `Abdomen`
- Properties:
  - `code_submission_value: String`: CDISC Submission code for the term.
  - `name_submission_value: String`: CDISC Submission name for the term.
  - `preferred_term: String`: The preferred term name.
  - `definition: String`: The CDISC definition of the term.
  - `synonyms: String[]`: A list of term synonyms.
Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  - `CONTAINS_ATTRIBUTES (Incoming, 1)`: A link to the CTPackageTerm for this term.

### CTTermNameRoot
- Description: A root object for the sponsor-defined control terminology term. It has one or multiple versions.
- Example: (no value, this node is a pointer)
- Properties:
  - `uid`: If the term is a template parameter value, a unique ID for the term.
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the sponsor-defined term. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the sponsor-defined term.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the sponsor-defined term.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the sponsor-defined term.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the sponsor-defined term.
  - `HAS_NAME_ROOT (Incoming, 1`): A pointer to the root term object.
 

### CTTermNameValue
- Description: A node representing an instance of a sponsor defined term, in a specific version.
- Example: `Novo Nordisk Location - Abdomen`
- Properties:
  - `name: String`: Name of the sponsor defined term.
  - `name_sentence_case: String`: Sentence-case formatted sponsor term name.
- Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  

### CodelistConfigRoot / FieldNameConfigRoot / SelectionRelTypeConfigRoot
- Description: An object representing a configured setting - a mapping between a config string and a CT codelist.
- Example: `CodelistConfig_000001 (study_field_name="StudyPopulation") => (codelist="CDISC Study Population")`
- Properties:
  - `uid`: a unique ID for the config parameter.
  - `study_field_name (optional)`: if the node is a `FieldNameConfigRoot`. the name of the study field to be mapped to a CT Codelist.
  - `study_selection_rel_type (optional)`: if the node is a `SelectionRelTypeConfigRoot`. the name of the relationship type to be mapped to a CT Codelist.

- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the codelist configuration. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the codelist configuration.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the codelist configuration.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the codelist configuration.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the codelist configuration.
 
### CodelistConfigValue
- Description: Properties of a selected configuration setting that maps study fields/selections to control terminology.
- Example: `Configuration for Study Population values`
- Properties:
  `sdtm_field: String`: The standard SDTM field name.
  `name: String`: A custom assigned name for the codelist.
  `sdtm_config: Boolean`: Whether to use the SDTM configuration.
  `sbmenu: String`: Which menu in the study builder the field is in.
  `sbtab: String` Which tab in the study builder the field is in.
  `tsparm: String`: Trial summary parameter information.
  `tsparcd: String`:  Additional trial summary information.
  `core: Boolean`: Whether the configuration value is a core value. 
  `order: Integer`: A configurable order for the configuration value.
  `notes: String`: Free text field for extra notes on this configuration.
- Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  - `HAS_CONFIGURED_CODELIST (Outgoing, 0..1`): The codelist root selected for this configuration value.
  
## Relationships
The following relationships are part of the control terminology model:

### CONTAINS_CATALOGUE / CONTAINS_CODELIST / CONTAINS_TERM
- Description: Relationships from the library to the control terminology catalogues, codelists and terms.
  `CONTAINS_CODELIST` denotes that the library *created* or *introduced* this codelist. It is not versioned. Even if a codelist is retired, the relationship remains there so that a library can/will contain retired codelists. Same for the `CONTAINS_TERM` relationship.
- Properties:
  - `none`
- Cardinality: `(0..*)`
- Start nodes: `Library`
- End nodes: `CTCatalogue`, `CTCodelistRoot`, `CTTermRoot`

### HAS_CONFIGURED_CODELIST
- Description: A relationship between a codelist configuration and the codelist that it selects.
- Properties:
  - `none`
- Cardinality: `(1..1)`
- Start nodes: `CodelistConfigValue`
- End nodes: `CTCodelistRoot`

### CONTAINS_PACKAGE
- Description: Links to the packages in a CT Catalogue.
- Properties:
  - `none`
- Cardinality: `(0..*)`
- Start nodes: `CTCatalogue`
- End nodes: `CTPackage`

### CONTAINS_CODELIST
- Description: Links to the loaded codelists in a loaded CT package.
- Properties:
  - `none`
- Cardinality: `(0..*)`
- Start nodes: `CTPackage`
- End nodes: `CTPackageCodelist`

### CONTAINS_TERM
- Description: Links to the loaded terms in a loaded package codelist.
- Properties:
  - `none`
- Cardinality: `(0..*)`
- Start nodes: `CTPackageCodelist`
- End nodes: `CTPackageTerm`

### CONTAINS_ATTRIBUTES
- Description: relationships between package codelist/terms, and the actual data-holding objects.
- Properties:
  - `none`
- Cardinality: `(1)`
- Start nodes: `CTPackageCodelist`, `CTPackageTerm`
- End nodes: `CTCodelistAttributesValue`. `CTTermAttributesValue`

### HAS_CODELIST
- Description: Connects the CT Catalogue to the list of codelists that it contains. It denotes that the catalogue *created* or *introduced* this codelist. It is not versioned. Even if a codelist is retired, the relationship remains there so that a catalogue can/will have retired codelists.
- Properties:
  - `none`
- Cardinality: `(0..*)`
- Start nodes: `CTCatalogue`
- End nodes: `CTCodelistRoot`

### HAS_ATTRIBUTES_ROOT
- Description: A link from the codelist/term root to its versioned attributes.
- Properties:
  - `none`
- Cardinality: `(1..1)`
- Start nodes: `CTCodelistRoot`, `CTTermRoot`
- End nodes: `CTCodelistAttributesRoot`, `CTTermAttributesRoot`


### HAS_NAME_ROOT
- Description: A link from the codelist/term root to its versioned sponsor defined name.
- Properties:
  - `none`
- Cardinality: `(1..1)`
- Start nodes: `CTCodelistRoot`, `CTTermRoot`
- End nodes: `CTCodelistNameRoot`, `CTTermNameRoot`


### HAS_TERM
- Description: Links a CT Codelist to the terms that it currently contains.
- Properties:
  - `start_date: DateTime`: When the term was added to the codelist.
  - `author_id: String`: Identifier of the user that added the term to the codelist.
  - `order: Integer`: The order of the term in the codelist.
- Cardinality: `(*..*)`
- Start nodes: `CTCodelistRoot`
- End nodes: `CTTermRoot`

### HAD_TERM
- Description: Links a CT Codelist to the terms that it contained in the past.
- Properties:
  - `start_date: DateTime`: When the term was added to the codelist.
  - `end_date: DateTime`: When the term was removed from the codelist.
  - `author_id: String`: Identifier of the user that removed the term from the codelist.
  - `order: Integer`: The old order of the term in the codelist.
- Cardinality: `(*..*)`
- Start nodes: `CTCodelistRoot`
- End nodes: `CTTermRoot`

### HAS_PARENT_TYPE / HAS_PARENT_SUB_TYPE
- Description: A relationship used to define an optional hierarchy of control terminology terms.
- Properties:
  - `none`
- Cardinality: `(0..*)`
- Start nodes: `CTTermRoot`
- End nodes: `CTTermRoot`

### LATEST_FINAL / LATEST_DRAFT / LATEST_RETIRED
- Description: Relationships between object roots and object versions in a given state: (Draft, final, or retired). Each root can have zero or one versions in each of these three states. (There is always only one latest draft, final version, or retired version)
- Properties:
   - `start_date: DateTime (Required)`: the date that the version was created.
   - `version: String (Required)`: the version number, e.g. 2.0.
   - `status: String (Optional)`: status message of the version.
   - `change_description: String (Optional)`: a description of what was changed in the version.
   - `author_id: String (Required)`: the ID of the user that created the version.
- Cardinality: `(0..1)`
- Start nodes: `CTCodelistAttributesRoot`, `CTCodelistNameRoot`, `CTTermAttributesRoot`, `CTTermNameRoot`, `CodelistConfigRoot`
- End nodes: `CTCodelistAttributesValue`, `CTCodelistNameValue`, `CTTermAttributesValue`, `CTTermNameValue`, `CodelistConfigValue`

### LATEST
- Description: A pointer to the latest version of the object, regardless of what state it is in.
- Properties:
   - (No properties)
- Cardinality: `(1)`
- Start nodes: `CTCodelistAttributesRoot`, `CTCodelistNameRoot`, `CTTermAttributesRoot`, `CTTermNameRoot`, `CodelistConfigRoot`
- End nodes: `CTCodelistAttributesValue`, `CTCodelistNameValue`, `CTTermAttributesValue`, `CTTermNameValue`, `CodelistConfigValue`

### HAS_VERSION
- Description: A relationship to each of the **previous** versions of an object. That is, if an object value is not a latest [draft, final, retired], it will be linked to the root using this relationship.
- Properties:
   - `start_date: DateTime (Required)`: the date that the version was created.
   - `end_date: DateTime (Required)`: the date that the version was replaced by a new version.
   - `version: String (Required)`: the version number, e.g. 2.0.
   - `status: String (Optional)`: status message of the version.
   - `change_description: String (Optional)`: a description of what was changed in the version.
   - `author_id: String (Required)`: the ID of the user that created the version.
- Cardinality: `(0..*)`
- Start nodes: `CTCodelistAttributesRoot`, `CTCodelistNameRoot`, `CTTermAttributesRoot`, `CTTermNameRoot`, `CodelistConfigRoot`
- End nodes: `CTCodelistAttributesValue`, `CTCodelistNameValue`, `CTTermAttributesValue`, `CTTermNameValue`, `CodelistConfigValue`



