---
title: Library Objects Data Model
date: 2021-08-06
---

# Library Objects Model
Library objects are objects defined within the context of the Clinical MDR library.
These objects can be then selected in studies, and take template parameters as extensions values.

Currently in scope library objects are objectives, endpoints and timeframes, as well as templates for these objects.

A snapshot of the part of the data model concerning library objects is shown below.
![Data Model Documentation](~@source/images/model/physical_data_model/snippet-library-object-model.png)

_The above image is a snapshot of the model as of May 28th, 2021._



## Terminology
**Objectives**, **Endpoints** and **Timeframes** are library objects that can be specified as part of a study design.
These objects exist within a library outside of the study scope.
This allows us to reuse objectives/endpoints/timeframes across different studies.

Key features of objectives, endpoints, timeframes:
- They are instantiated from template strings, and filled in with template parameter values.
    - For example, consider the following objective template: `demonstrate superiority of [Compound] over [Compound] for the purpose of [SpecialPurpose].`
    - An instantiated objective could be `To demonstrate superiority of [Metformin] over [Insulin] for the purpose of [Treating Diabetes]`.
    - Here, [Compound] and [SpecialPurpose] are template parameters, and [Metformin], [Insulin] and [Treating Diabetes] are template parameter values.
- They are versioned objects inside the Neo4j graph, allowing us to get a full version history for them.
- They can be selected in a study (See `Study Selection` in the study data model documentation).


## Business Logic

### Versioning and Audit Trails
One of the main design element in the physical Neo4j data model is the support for full versioning and audit trail capabilities. 
This is achieved by separating nodes that identify data elements from the data element values, and capture all of the data state attributes as relationship properties between the identifier and value nodes.
The identifier nodes will have the 'Root' post fix in their name, and the value nodes 'Value' as their name post fix. 
All the state attributes as action, timestamps, user names, change description etc. will be saved as part of relationship properties.

![Data Model Documentation](~@source/images/model/physical_data_model/versioning-state-transition-table.png)
![Data Model Documentation](~@source/images/model/physical_data_model/versioning-state-action-diagram.png)


An object will always be in one of the following states:
- `DRAFT`: still being edited, not yet usable by the application.
- `FINAL`: a released state, this means the object can be used in the application.
- `RETIRED`: a soft-delete of the object, it is now disabled and can no longer be used.

The **audit trail** is a list of versions that can be constructed from the history of a library object, based on the versions in the graph.
This version history will contain all edits to the object: 
- Who changed it.
- When it was changed.
- What was changed.

![Data Model Documentation](~@source/images/model/physical_data_model/versioning-process-flow.png)

### Cascading Updates for Library Objects
> This section describes the concept of how cascading updates work in the case of Objective Templates.
> However, for Endpoint Templates and Timeframe Templates the concept is the same.

When an Objective Template is approved for the first time (target version=1.0):
No cascading update will be done. By design, no Objective can be linked with an
Objective Template in version `0.x`. I.e., no update is needed at all.

When an Objective Template is approved for the second or any subsequent time (target version>1.0):
A cascading update will be done as follows:

* For every objective that was created out of the objective template
  (cf. `(templateRoot)-[:HAS_OBJECTIVE]->(objectiveRoot)`):
  * Increase the version(s) of the objective:
    * If there is a Draft version: Create a new Draft version increased by 0.1.
    * If there is a Final or Retired version: Create a new Final or Retired version increased by 1.0.
    * _It is possible to have both, a Draft and a Final version. In that case, both versions will be
      increased._
    * _Independent of the status:_
    * The objective value will be updated to hold the new value for the Objective Template with all
      Template Parameter values represented with the same values as in the previous version.
      _Since the parameters cannot be changed after the first approval of a template, only the surrounding
      text will be updated._
    * The `end_date` (existing version) and `start_date` (new version) properties will be updated
      accordingly with the same datetime value as for the Objective Template approval.
    * The change description will be set to: "Cascading update based on a new Objective Template
      version."
      
### Consistency / Locking on edits of library objects
In order to keep the graph consistent, the following procedure will be used:
1. Acquire a lock on the one `ObjectiveTemplateRoot` node (that shall be approved).
2. Acquire a lock on each of the related `ObjectiveRoot` nodes.
3. Approve the objective template including the cascading update changes.
4. Release the locks: Either all at once or first the locks from step 2 and then the locks from step 1.



## Node Labels
The following node labels are part of the library objects data model:

### Library
- Description: an instance of a library holding objectives, endpoints, timeframes, assessments and other library elements.
- Example: Sponsor Library
- Properties: 
  - `name: String (Required, Unique)`: An unique name (identifier) for the library.
  - `is_editable: Boolean`: Whether the library can be edited (e.g. new objectives can be added.)
- Relationships:
  - `CONTAINS_OBJECTIVE_TEMPLATE (Outgoing, 0..*)`: links to each of the objective templates in the library. 
  - `CONTAINS_OBJECTIVE (Outgoing, 0..*)`: links to each of the objectives in the library. 
  - `CONTAINS_ENDPOINT_TEMPLATE (Outgoing, 0..*)`: links to each of the endpoint templates in the library. 
  - `CONTAINS_ENDPOINT (Outgoing, 0..*)`: links to each of the endpoints in the library. 
  - `CONTAINS_TIMEFRAME_TEMPLATE (Outgoing, 0..*)`: links to each of the timeframe templates in the library. 
  - `CONTAINS_TIMEFRAME (Outgoing, 0..*)`: links to each of the timeframes in the library. 
  - `CONTAINS_CATALOGUE (Outgoing, 0..*)`: links to each of the Control Terminology Catalogues in the library.
  - `CONTAINS_CODELIST (Outgoing, 0..*)`: links to each of the Control Terminology Codelists in the library.
  - `CONTAINS_TERM (Outgoing, 0..*)`: links to each of the Control Terminology Terms  in the library. 
  - `CONTAINS_ASSESSMENT (Outgoing, 0..*)`: links to each of the assessments (template parameters) in the library. 
  - `CONTAINS_INDICATION (Outgoing, 0..*)`: links to each of the indications (template parameters) in the library. 


### ObjectiveTemplateRoot 
- Description: a root object for an objective template, containing links to all versions of that given template. The template is used for initializing objectives with set template parameter values.
- Example: ObjectiveTemplate_000001
- Optional labels: 
  - `DeletedObjectiveTemplateRoot` if the objective template was (soft-)deleted.
- Properties: 
  - `uid: String (Required, Unique)`: An auto-generated, unique string identifier for the objective template.
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the objective template. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the objective template.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the objective template.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the objective template.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the objective template.
  - `HAS_OBJECTIVE (Outgoing, 0..*)`: links to each of the objectives instantiated from a template.
  - `OT_USES_PARAMETER (Outgoing, 0..*)`: Links to template parameters that can be used in this template (at a given position).
  - `CONTAINS_OBJECTIVE_TEMPLATE (Incoming, 1)`: a link to the library that the objective template belongs to.
  
### ObjectiveTemplateValue
- Description: a text string representing a template for objectives.
- Example: To demonstrate superiority of [Compound] over [Compound] for the purpose of [SpecialPurpose].
- Properties:
  - `name: String (Required, Indexed)`: The format of the template string.
- Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root template that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root template that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root template that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root template that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root template that this value is a latest retired version of.
  
  
### ObjectiveRoot
- Description: a root object for a single objective, containing links to all versions of that given objective.
- Example: Objective_000001
- Optional labels: 
  - `DeletedObjectiveRoot` if the objective was (soft-)deleted.
- Properties: 
  - `uid: String (Required, Unique)`: An auto-generated, unique string identifier for the objective.
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the objective. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the objective.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the objective.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the objective.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the objective.
  - `CONTAINS_OBJECTIVE (Incoming, 1)` a link to the library that the objective belongs to. Expected number of objectives per template (~20-100)
  - `HAS_OBJECTIVE (Incoming, 1)` a link to the template that the objective was instantiated from.
  
### ObjectiveValue
- Description: a text string representing the general aim of a study.
- Example: To demonstrate superiority of [Metformin] over [Insulin] for the purpose of [Treating Diabetes].
- Properties:
  - `name: String (Required, Indexed)`: The name of the objective (generated from the template)
- Relationships:
  - `OV_USES_VALUE (Outgoing, 0..*)`: A link to a template parameter used in the objective (with position and index).
  - `HAS_CONJUNCTION (Outgoing, 0..*)`: A link to a conjunction word used in the objective (with position).
  - `HAS_SELECTED_OBJECTIVE (Incoming, 0..*)`: Pointer to where this value is used in a specific study objective object.
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  
### EndpointTemplateRoot
- Description: a root object for an endpoint template, containing links to all versions of that given template. The template is used for initializing endpoints with set template parameter values.
- Example: EndpointTemplate_000001
- Optional labels: 
  - `DeletedEndpointTemplateRoot` if the endpoint template was (soft-)deleted.
- Properties: 
  - `uid: String (Required, Unique)`: An auto-generated, unique string identifier for the endpoint template.
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the endpoint template. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the endpoint template.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the endpoint template.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the endpoint template.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the endpoint template.
  - `HAS_ENDPOINT (Outgoing, 0..*)`: links to each of the endpoints instantiated from a template.
  - `ET_USES_PARAMETER (Outgoing, 0..*)`: Links to template parameters that can be used in this template (at a given position).
  - `CONTAINS_ENDPOINT_TEMPLATE (Incoming, 1)`: a link to the library that the endpoint template belongs to.
  
### EndpointTemplateValue
- Description: a text string representing a template for endpoints.
- Example: To identify the effect of [CompoundDosing] on the number of red blood cells.
- Properties:
  - `name: String (Required, Indexed)`: The format of the template string.
- Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root template that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root template that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root template that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root template that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root template that this value is a latest retired version of.
  
  
### EndpointRoot 
- Description: a root object for a single endpoint, containing links to all versions of that given endpoint.
- Example: Endpoint_000001
- Optional labels: 
  - `DeletedEndpointRoot` if the endpoint was (soft-)deleted.
- Properties: 
  - `uid: String (Required, Unique)`: An auto-generated, unique string identifier for the endpoint.
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the endpoint. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the endpoint.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the endpoint.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the endpoint.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the endpoint.
  - `CONTAINS_ENDPOINT (Incoming, 1)` a link to the library that the endpoint belongs to. Expected number of endpoints per template (~20-100)
  - `HAS_ENDPOINT (Incoming, 1)` a link to the template that the endpoint was instantiated from.
  
### EndpointValue
- Description: a text string representing the general aim of a study.
- Example: To identify the effect of [100mg Insulin] on the number of red blood cells. 
- Properties:
  - `name: String (Indexed)`: The name of the endpoint (generated from the template)
- Relationships:
  - `EV_USES_VALUE (Outgoing, 0..*)`: A link to a template parameter used in the endpoint (with position and index).
  - `HAS_CONJUNCTION (Outgoing, 0..*)`: A link to a conjunction word used in the endpoint (with position).
  - `HAS_SELECTED_ENDPOINT (Incoming, 0..*)`: Pointer to where this value is used in a specific study endpoint object.
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  
### TimeframeTemplateRoot
- Description: a root object for a timeframe template, containing links to all versions of that given template. The template is used for initializing timeframes with set template parameter values.
- Example: TimeframeTemplate_000001
- Optional labels: 
  - `DeletedTimeframeTemplateRoot` if the timeframe template was (soft-)deleted.
- Properties: 
  - `uid: String (Required, Unique)`: An auto-generated, unique string identifier for the timeframe template.
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the timeframe template. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the timeframe template.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the timeframe template.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the timeframe template.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the timeframe template.
  - `HAS_TIMEFRAME (Outgoing, 0..*)`: links to each of the timeframes instantiated from a template.
  - `TT_USES_PARAMETER (Outgoing, 0..*)`: Links to template parameters that can be used in this template (at a given position).
  - `CONTAINS_TIMEFRAME_TEMPLATE (Incoming, 1)`: a link to the library that the timeframe template belongs to.
  
### TimeframeTemplateValue
- Description: a text string representing a template for timeframes.
- Example: To identify the effect of [CompoundDosing] on the number of red blood cells.
- Properties:
  - `name: String (Required, Indexed)`: The format of the template string.
- Relationships:
  - `HAS_VERSION (Incoming, 1)`: The root template that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root template that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root template that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root template that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root template that this value is a latest retired version of.
  
  
### TimeframeRoot  
- Description: a root object for a single timeframe, containing links to all versions of that given timeframe.
- Example: [...................]
- Optional labels: 
  - `DeletedTimeframeRoot` if the timeframe was (soft-)deleted.
- Properties: 
  - `uid: String (Unique)`: An auto-generated, unique string identifier for the timeframe.
- Relationships:
  - `HAS_VERSION (Outgoing, 0..*)`: links to different versions of the timeframe. 
  - `LATEST (Outgoing, 1`): A pointer to the latest value of the timeframe.
  - `LATEST_FINAL (Outgoing, 1`): A pointer to the latest final version of the timeframe.
  - `LATEST_DRAFT (Outgoing, 1`): A pointer to the latest draft version of the timeframe.
  - `LATEST_RETIRED (Outgoing, 1`): A pointer to the latest retired version of the timeframe.
  - `CONTAINS_TIMEFRAME (Incoming, 1)` a link to the library that the timeframe belongs to. Expected number of timeframes per template (~20-100)
  - `HAS_TIMEFRAME (Incoming, 1)` a link to the template that the timeframe was instantiated from.
  
### TimeframeValue
- Description: a text string representing the general aim of a study.
- Example: [...................]
- Properties:
  - `name: String (Indexed)`: The name of the timeframe (generated from the template)
- Relationships:
  - `TV_USES_VALUE (Outgoing, 0..*)`: A link to a template parameter used in the timeframe (with position and index).
  - `HAS_CONJUNCTION (Outgoing, 0..*)`: A link to a conjunction word used in the timeframe (with position).
  - `HAS_SELECTED_TIMEFRAME (Incoming, 0..*)`: Pointer to where this value is used in a specific study endpoint object.
  - `HAS_VERSION (Incoming, 1)`: The root object that this value is a version of.
  - `LATEST (Incoming, 0..1`):  The root object that this value is a latest version of.
  - `LATEST_FINAL (Incoming, 0..1`): The root object that this value is a latest final version of.
  - `LATEST_DRAFT (Incoming, 0..1`): The root object that this value is a latest draft version of.
  - `LATEST_RETIRED (Incoming, 0..1`): The root object that this value is a latest retired version of.
  
### Conjunction
- Description: conjunctions are words used to seperate lists of template parameters when used in a template. For example, if the template string is "to measure the effect of [Compound]", an object instantiation could be "to measure the effect of [Metformin and Insulin]". In this case, the conjunction word is "and". 
- Example: a valid conjunction is one of ["and", "or", ","].
- Properties:
  - `string: String (Unique)`: The conjunction word/string. 
- Relationships:
  - `HAS_CONJUNCTION (Incoming, 0..*`): points to an objective, endpoint or timeframe value that uses this conjunction at a certain position in the template.
  

## Relationship Types
The following relationship types are part of the library objects data model:

### CONTAINS_TERM
- Description: Relationships between `Library` nodes and `CTTermRoot` nodes. Indicates that a term exists within a given library, as a template parameter.
- Properties:
  - (No properties)
- Cardinality: `(1..*)`
- Start nodes: `Library`
- End nodes: `CTTermRoot`

### CONTAINS_INDICATION / CONTAINS_ASSESSMENT 
- Description: Relationships between `Library` nodes and `TemplateParameterValueRoot` nodes. Indicates that a template parameter exists within a given library.
- Properties:
  - (No properties)
- Cardinality: `(1..*)`
- Start nodes: `Library`
- End nodes: `AssessmentRoot`, `IndicationRoot`


### CONTAINS_OBJECTIVE / CONTAINS_OBJECTIVE_TEMPLATE / CONTAINS_ENDPOINT / CONTAINS_ENDPOINT_TEMPLATE / CONTAINS_TIMEFRAME / CONTAINS_TIMEFRAME_TEMPLATE
- Description: Relationships between `Library` nodes and library objects. Used to establish in which library the objects are placed.
- Properties:
  - (No properties)
- Cardinality: `(1..*)`
- Start nodes: `Library`
- End nodes: `ObjectiveTemplateRoot`, `ObjectiveRoot`, `EndpointTemplateRoot`, `EndpointRoot`, `TimeframeTemplateRoot`, `TimeframeRoot`


### HAS_SELECTED_OBJECTIVE / HAS_SELECTED_ENDPOINT / HAS_SELECTED_TIMEFRAME
- Description: links between a study and library object values. See the *Study Data Model* documentation for more information.
- Properties:
  - (No properties)
- Cardinality: `(*..1)`
- Start nodes: `StudyObjective`, `StudyEndpoint`
- End nodes: `Objective Value`, `Endpoint Value`, `Timeframe Value`

### LATEST_FINAL / LATEST_DRAFT / LATEST_RETIRED
- Description: Relationships between object roots and object versions in a given state: (Draft, final, or retired). Each root can have zero or one versions in each of these three states. (There is always only one latest draft, final version, or retired version)
- Properties:
   - `start_date: DateTime (Required)`: the date that the version was created.
   - `version: String (Required)`: the version number, e.g. 2.0.
  - `status: String (Optional)`: status message of the version.
   - `change_description: String (Optional)`: a description of what was changed in the version.
   - `author_id: String (Required)`: the ID of the user that created the version.
- Cardinality: `(0..1)`
- Start nodes: `ObjectiveTemplateRoot`, `ObjectiveRoot`, `EndpointTemplateRoot`, `EndpointRoot`, `TimeframeTemplateRoot`, `TimeframeRoot`
- End nodes: `ObjectiveTemplateValue`, `ObjectiveValue`, `EndpointTemplateValue`, `EndpointValue`, `TimeframeTemplateValue`, `TimeframeValue`

### LATEST
- Description: A pointer to the latest version of the object, regardless of what state it is in.
- Properties:
   - (No properties)
- Cardinality: `(1)`
- Start nodes: `ObjectiveTemplateRoot`, `ObjectiveRoot`, `EndpointTemplateRoot`, `EndpointRoot`, `TimeframeTemplateRoot`, `TimeframeRoot`
- End nodes: `ObjectiveTemplateValue`, `ObjectiveValue`, `EndpointTemplateValue`, `EndpointValue`, `TimeframeTemplateValue`, `TimeframeValue`


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
- Start nodes: `ObjectiveTemplateRoot`, `ObjectiveRoot`, `EndpointTemplateRoot`, `EndpointRoot`, `TimeframeTemplateRoot`, `TimeframeRoot`
- End nodes: `ObjectiveTemplateValue`, `ObjectiveValue`, `EndpointTemplateValue`, `EndpointValue`, `TimeframeTemplateValue`, `TimeframeValue`


### OT_USES_PARAMETER / ET_USES_PARAMETER / TT_USES_PARAMETER
- Description: A relationship from an object template to a template parameter (class). It indicates that a specific template parameter (e.g. `Compound`) needs to be used at a specific position in the template.
- Properties:
  - `position: Integer (Required)`: the position in the template that the template parameter should be in.
  - `allow_multiple: Boolean (Required)`: Whether multiple template parameter values of the the type can be used in the slot.
  - `allow_none: Boolean (Required)`: Whether the template parameter can be left empty in the library object instantiation.
- Cardinality: `(0..*)`
- Start nodes: `ObjectiveTemplateRoot`, `EndpointTemplateRoot`, `TimeframeTemplateRoot`
- End nodes: `TemplateParameter`

### OV_USES_VALUE / EV_USES_VALUE / TV_USES_VALUE
- Description: A relationship from a library object to a template parameter value. It indicates that a specific template value (e.g. `Metformin`) is used in an instantiation of a library object, in a given position with a specific index.
- Properties:
  - `position: Integer (Required)`: the position in the template that the template parameter value is in.
  - `index: Integer (Required)`: In case multiple template parameter values sit within the same slot of a template, the index of the value in that given slot. (If multiple values sit in the same slot, a `HAS_CONJUNCTION` relationship will be present)
- Cardinality: `(0..*)`
- Start nodes: `ObjectiveValue`, `EndpointValue`, `TimeframeValue`
- End nodes: `TemplateParameterValueRoot`

### HAS_CONJUNCTION
- Description: When multiple template parameter values sit within the same slot of an object template, this relationship specifies the conjunction word used to connect them. 
- Examples: `and`, `or`, or `,`.
- Properties:
  - `position: Integer (Required)`: the position in the template that the conjunction word is used in.
- Cardinality: `(0..*)`
- Start nodes: `ObjectiveValue`, `EndpointValue`, `TimeframeValue`
- End nodes: `Conjunction`

