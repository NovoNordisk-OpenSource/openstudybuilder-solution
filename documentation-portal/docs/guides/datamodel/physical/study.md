---
title: Study Data Model
date: 2021-06-06
---

# Study Data Model
In the graph, the representation of a study (including its history & selections) 
is a set of nodes and relationships. To embed the complex, nested structure of a study, several node labels and relationship types are used.
To record the history of studies, including their selections and fields, a special type of versioning logic is implemented.
This is [documented here](#studyversioning).

The image below shows the part of the physical model relating to studies and study versioning.
![Neo4j Model for Study Versioning](~@source/images/model/physical_data_model/study-model.png)



## Terminology
The following terminology is used when describing the study representation in the graph.

| Concept          | Description                                                                                                                                                                                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Clinical Programme   | A programme that contains one or more projects.                                                                                                                  |
| Project          | A project that contains one or more studies.                                                                                                                                                                |
| Study Root       | A reference to the study, containing the unique identifier.                                                                                                                                                                |
| Study State      | State of a study value. One of [Draft, Released, Locked, Deleted].                                                                                                                                                         |
| Study Value      | A representation of a study in a given state.  A StudyRoot may have several StudyValues, each value has a single StudyState.                                                                                               |
| Study Properties | Study identifiers. These are stored on the StudyValue node.                                                                                                                                                |
| Study Fields     | Non-versioned properties of a study. Examples are registry identifiers or projects.                                                                                                                                        |
| Study Selections | Any selection made by a study. StudyObjectives, StudyEndpoints, StudyCompounds are examples of Study Selections. Selections are ordered, and can have a level.                                                             |
| Audit Trail      | A ‘log’ of how a study was modified over time. The audit trail contains edits of study properties, study fields, study selections, and state changes of the study (e.g. releases).                           |
| Study Actions    | An action represents a single change made to a study. Some examples are “Edit”, “Release” or “Delete”. An action record will contain the objects the action was performed on. An audit trail is a ordered list of actions. |

### Study Properties
Study properties are the identifiers of a study. These are stored directly on the StudyValue node.
The set of properties should be kept minimal, and is assumed to be rarely changed.
Changing the study properties is a costly operation in the graph. 

Example study properties:
```
uid: String
study_number: String
study_id: String
study_acronym: String
```

> Study nodes will be ‘thin’, only containing the identification properties of the study. Any other (unversioned) fields of the study will be a separate study field node.

### Study Selections
Study selections are the versioned library elements selected for a study. (Objectives, Endpoints, etc.) 
These can optionally have a level assigned to them. Selections for a given type are always ordered.
Selections are materialized as separate nodes in the graph. Each selection node can then have three nodes linked to it:
- The study the selection is for (a StudyValue node)
- A value of a library element (e.g. an ObjectiveValue node)
- A selection level (e.g. an ObjectiveLevel node)

Selection nodes are intended to be used as pointers, they do not have any properties assigned to them besides the order. Study Selections will have a `HAS_SELECTED_XXXX` relationship to the library element that contains a selection date property.

#### Deleting Selections
Consider the case where a study selection gets deleted, and that selection is linked to other study selections. For example, a study objective with linked study endpoints. On deletion of the study objective, no other selections are deleted, only the links from the study objective to the study endpoints are removed.

### Study Fields
Unlike selections, study fields represent links to unversioned library elements. These include projects, registry identifiers, selected populations and others.

In principle, study fields represent data that is logically stored together with the study.
In the graph however, these are not in the StudyValue, but rather as separate nodes. This allows for a cleaner, easier to maintain audit trail. 
In addition, this lets the domain layer be flexible in assigning different sets of fields (like key/value pairs) to a study.

Study fields have no order, and do not contain a selection date explicitly in the graph.
Study field values can be `null`, if this is the case, the study field nodes will have a relationship to a `NullValueReason` node.

The image below (see Section 'Neo4j Data Model') shows how studies, study selections and study fields are modeled in the graph.

### Study Actions
An `Action` node in the graph represents an item in the audit trail.
An `Action` node has one extra label (`Edit`, `Create`, ...)  to track the type of action performed.
Actions will have outgoing relationships to the elements changed during that action.

An action node may only have a single `BEFORE` and a single `AFTER` relationship linked to it.
If multiple study fields/selections are changed in a single edit operation, this will result in multiple study actions in the graph.
Outgoing `BEFORE`/`AFTER` relationships will have an `index` property on them, so that we can trace back which values replaces another.

### Operations on Studies
With this terminology in mind, the API must be able to:
- Retrieve an ordered list of study actions (Audit Trail) for a study.
- Distinguish and log different types of actions.
- Represent multiple versions of a study.
- Distinguish between the different versions of a study root:
  - (0...1) releases
  - (0...1) latest drafts
  - (0...1) latest locked versions
  - (0...n) locked versions
  - (1...n) old drafts
  - (0...1) deleted versions
  
The next sections will describe in detail how each of these components of the conceptual study view are defined.


## Business Logic
The following (sub)sections describe how the business logic around studies translates to operations on the graph data.

### <a name="studyversioning"></a>Study Versioning Logic
Study versioning is fundamentally different from versioning library elements. 
The below state diagram expresses how a study changes state after certain operations are performed.
Note the differences between the library element state diagram as presented in the previous page of the documentation portal.

![Study state diagram](~@source/images/model/physical_data_model/studystatediagram.png)

The next sections detail the graph transformations that take place on each of these state transitions.


#### 1. Create Study
```
State Before: None
Action: Create
State After: Draft
```

![Study state diagram](~@source/images/model/physical_data_model/studycreate.png)


When creating a new study, we create a new `StudyRoot` as well as an initial draft `StudyValue`. 
As part of the create, three types of study attributes can be specified:
- *Study Properties* (identifiers)
- *Study Fields* (Unversioned study metadata - such as the project, or study population) 
- *Study Selections* (Versioned study metadata - such as objectives/endpoints)

The following transformations take place in the graph:
- Create a StudyRoot `(root)` with a new UID.
- Create a StudyValue draft `(d)`. Set study properties on the node.
- If applicable, create `StudySelection` nodes pointing to the versioned object and levels.
- Link `(d)` to selections with a `HAS_SELECTION` relationship. (StudySelection nodes).
- Link `(d)` to  fields with a `HAS_FIELD` relationship (StudyField nodes).
- Link `(root)` and `(d)` with a `LATEST_DRAFT` relationship.
- Link `(root)` and `(d)` with a `HAS_DRAFT` relationship.

Update the audit trail:
- Create a node `(e:Action:Create)` with the current timestamp.
- Create a relationship `(root)-[:AUDIT_TRAIL]->(e)`.
- Create an `AFTER` relationship from `(e)` to the new value `(d)`,
- Create `AFTER` relationships from `(e)` to each of the StudySelections.
- Create `AFTER` relationships from `(e)` to each of the StudyFields.

#### 2a. Edit Study Selections
```
State Before: Draft
Action: Edit Selection
State After: Draft
```

![Study state diagram](~@source/images/model/physical_data_model/studyedita.png)

When a draft edit involves the change of study selections, the graph is modified as follows:

Consider a draft edit. Let `(root)` be the root, `(d)` be the existing draft node. The study must be in a draft state.

Graph transformations:
- Create new study selection nodes, pointing to the relevant library objects. Ensure the order is set correctly.

- For each of the removed selections, delete the `HAS_SELECTION` relationship coming in from the study value node `(d)`.
- For each of the created selections, add a `HAS_SELECTION` relationship, coming in from the study value node (d).

Maintain the audit trail:
- Create a new node `(e:StudyAction:Edit)` with the current timestamp.
- Create a relationship `(root)-[:AUDIT_TRAIL]->(e)`.
- Let `(e)` point to the added selections with an `AFTER` relationship.
- Let `(e)` point to the removed selections with a `BEFORE` relationship.


> If selections have been replaced, ensure that the index property on the BEFORE/AFTER relationships match. For example, if “Selection 1” was replaced by “Selection 2”, the BEFORE relationship to “Selection 1” should have the same index as the AFTER relationship to “Selection 2”. 

#### 2b. Edit Study Fields
```
State Before: Draft
Action: Edit Study Field
State After: Draft
```

![Study state diagram](~@source/images/model/physical_data_model/studyeditb.png)


When a draft edit involves the change of study fields, the graph is modified similar to study selection changes.
Consider a draft edit. Let `(root)` be the root, `(d)` be the existing draft node. The study root must not have any `LATEST_LOCKED` or `DELETED` relationships.

Graph transformations:
- Create new study field nodes if they do not exist. (Merge in the graph).
- For each of the removed fields, delete the `HAS_FIELD` relationship, coming in from the study value node `(d)`.
- For each of the created fields, add a `HAS_FIELD` relationship, coming in from the study value node `(d)`.

- Create a new `(e:StudyAction:Edit)` with the current timestamp.
- Create a relationship `(root)-[a:AUDIT_TRAIL]->(e)`.
- Let `(e)` point to the added fields with an AFTER relationship.
- Let `(e)` point to the removed fields with a BEFORE relationship.

> If fields have been replaced, ensure that the index property on the BEFORE/AFTER relationships match. For example, if “Field 1” was replaced by “Field 2”, the BEFORE relationship to “Field 1” should have the same index as the AFTER relationship to “Field 2”. 

#### 2c. Edit Study Properties
```
State Before: Draft
Action: Edit Study Properties
State After: Draft
```


![Study state diagram](~@source/images/model/physical_data_model/studyeditc.png)

Study properties (identifiers) are expected to rarely change.
Although the operation of changing properties is expensive, we take the following approach to be as optimal as possible.
The approach below minimizes the number of relationship creates/deletes.

Consider a draft edit. Let `(root)` be the root, `(d1)` be the existing draft node. The study root must not have any `LATEST_LOCKED` relationships or any `DELETED` relationships. (e.g. it is draft state).

- Create a new StudyValue node `(d2)`.
- Copy over the properties from `(d1)` to `(d2)`.
- update the properties on `(d1)` to be the newly selected ones.

> We’re now repurposing (d1) as our ‘updated value’, whereas (d2) will represent the old value for the audit trail. Instead of using node `(d2)` for our new draft, we repurpose `(d1)`. This avoids moving all the `HAS_SELECTION`/`HAS_FIELD` relationships attached to `(d1)`.

We are now in the following state:
1. `(d2)` is disconnected from the graph.
2. `(d1)` is connected to many elements in the graph. (fields/selections)
3. `(d1)` has `AFTER` relationship(s) incoming from previous StudyActions `(e)`.

Next, we make sure that the previous StudyAction `(e)` (which was pointing to `(d1)`) now point to `(d2)`. Now, `(d1)` and `(d2)` have effectively switched places completely. 

Then:
- Create a node `(e2:Action:Edit)` with the current timestamp.
- Create a relationship `(root)-[a:AUDIT_TRAIL]->(e2)`.
- Let `(e2)` point to the new draft `(d1)` with an `AFTER` relationship.
- Let `(e2)` point to the old draft `(d2)` with a `BEFORE` relationship.

#### 3. Release
```
State Before: Draft
Action: Release
State After: Draft & Released
```

![Study state diagram](~@source/images/model/physical_data_model/studyrelease.png)

Consider that we have a draft study node `(d)`. Then, we create a release.

- Create a new StudyValue node `(r)`. This will be the released version.
- If a `RELEASED` relationship already exists from the root, delete it. Old releases are not stored by relationships to the root.
- from the root, create a `RELEASED` relationship to `(r)`.
- Copy over all properties from the draft node `(d)` to the release node `(r)`.
- Copy all existing selection & field relationships from the old draft node to the released node.

Maintain the audit trail:
- Create an `(e:Action:Release)` with the current timestamp.
- Create a relationship `(root)-[a:AUDIT_TRAIL]->(e)`.
- Create a `BEFORE` relationship from `(e)` to `(d)`.
- Create an `AFTER` relationship from `(e)` to `(r)`.


#### 4. Lock & Release
```
State Before: Draft
Action: Lock & Release
State After: Locked & Released
```

> Unlike other versioned graph elements, locking a study implies an automatic release. A lock action will always trigger a release - this is to prevent the latest release from being an older version than the latest locked.

![Study state diagram](~@source/images/model/physical_data_model/studylock.png)

A lock operation always triggers a release. This is to ensure that the latest locked version will never be newer than the latest release.
When a draft gets locked, the study is no longer editable.

Graph Transformations:
- Remove the `HAS_DRAFT` and `LATEST_DRAFT` relationships incoming to `(d)`.
- Add a `LATEST_LOCKED` and a `LOCKED` relationship from the root to `(d)`.
- Add a `RELEASED` relationship from the root to `(d)`.
  
Maintain the audit trail:
- Create a node `(e:Action:Lock)` with the current timestamp.
- Create a relationship `(root)-[a:AUDIT_TRAIL]->(e)`.
- Create a `BEFORE` relationship from `(e)` to `(d)`.
- Create an `AFTER` relationship from `(e)` to `(d)`.

> From a graph perspective, no new study values are created - the latest draft (d) will just get different relationships. This is why the (e:Release:Action) node points twice to the same StudyValue.

#### 5. Unlock
```
State Before: Locked
Action: Unlock
State After: Draft
```

![Study state diagram](~@source/images/model/physical_data_model/studyunlock.png)

In the graph, unlock a node is more complicated than locking a node:
We need to create a new study value node so that the old locked version is preserved in the audit trail.

Let `(lock)` be the previously locked and release node.

Graph transformations:
- Remove the `LATEST_LOCKED` relationship from the root to `(lock)`.
- Create a new StudyValue node `(d2)`. This will be the unlocked draft version.
- Create a `LATEST_DRAFT` & `HAS_DRAFT` relationship to `(d2)`.
- Copy over all study properties from the locked node `(lock)` to the new draft `(d2)`.
- Copy all existing `HAS_FIELD`/`HAS_SELECTION` relationships from the locked node to the draft node.

Maintain the audit trail:
- Create an `(e:Action:Unlock)` node with the current timestamp.
- Create a relationship `(root)-[a:AUDIT_TRAIL]->(e)`.
- Let `(e)` point to the new draft `(d2)` with an `AFTER` relationship.
- Let `(e)` point to the old locked version `(d1)` with a `BEFORE` relationship.

#### 6. Soft-Delete
```
State Before: Draft
Action: Soft-Delete
State After: Deleted
```

> A soft-delete implies that a StudyRoot will become inactive indefinitely. There is currently no way to reopen deleted studies.

![Study state diagram](~@source/images/model/physical_data_model/studydelete.png)


Graph Transformations:
- For the deleted study, we switch out the `StudyRoot` label for the `StudyRootDeleted` label.
- Given latest draft `(d)`, we switch out the `HAS_DRAFT` and `LATEST_DRAFT` relationships for a `DELETED` relationship.

Maintain the audit trail:
- Create a node `(e:Action:Delete)` with the current timestamp.
- Create a relationship `(root)-[a:AUDIT_TRAIL]->(e)`.
- Let `(e)` point to draft `(d)` with an `AFTER` relationship.
- Let `(e)` point to draft `(d)`  with a `BEFORE` relationship.

There are prerequisites for performing a soft-delete:
- The study must have never been released.
- The study must have never been locked.


#### 7. Clone
```
State Before: Draft
Action: Clone
State After: Draft
```

![Study state diagram](~@source/images/model/physical_data_model/studyclone.png)


Cloning a draft means:
- creating a new `StudyRoot` & `StudyValue`. The new StudyValue will take over the properties of the cloned StudyValue.
- Creating new `StudySelection` nodes that point to the same library elements as the original StudySelection nodes.
- Linking the new `StudyValue` to all previously selected `StudyFields`.

Let `(r)` be a study root. Let `(d)` be the latest draft.

Graph transformations:
- Create a new root `(r2)`. Create a new draft `(d2)`.
- Copy all study properties on node `(d)` over to `(d2)`. 
- Link the new root `(r2)` to `(d2)` with `LATEST_DRAFT` and `HAS_DRAFT` relationships.
- Copy all study selection nodes attached to `(d)` into new nodes. Attach them all to `(d2)`. Link the new study selections to the original library elements that `(d)` was selecting.
- Attached `(d2)` to the original study fields that `(d)` was selecting.

Maintain the audit trail:
- Create an `(e:Action:Clone)` node with the current timestamp.
- Create a relationship `(r)-[a:AUDIT_TRAIL]->(e)`.
- Create a relationship `(r2)-[a2:AUDIT_TRAIL]->(e)`.
- Let `(e)` point to the old draft `(d)` with an `BEFORE` relationship.
- Let `(e)` point to the old study selections/study fields with a `BEFORE` relationship.
- Let `(e)` point to the new draft `(d2)` with an `AFTER` relationship.
- Let `(e)` point to the new study selections/study fields with a `AFTER` relationship.

> Ensure that the index properties on the `BEFORE`/`AFTER` relationships are synced, such that the index of the field in the original study is the same as the index of the field in the new study. 

## Node Labels
### ClinicalProgramme
- Description:  The highest level in the study hierarchy. A clinical programme contains several projects, which contain several studies.
- Example: "CP_001"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the clinical programme.
  - `name: String (Required, Unique)`: A human-readable name for the programme.
- Relationships:
  - `HOLDS_PROJECT (Outgoing, 0..*)`: links to each of the projects as part of the programme.

### Project
- Description:  A project (in a programme) that can be linked to a study, via a StudyProjectField. 
- Example: "Project_000001"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the project.
  - `project_number: String (Required, Unique)`: A unique number for the project.
  - `name: String (Required, Unique)`: A unique name for the project.
  - `brand_name: String`: The brand that the project was created for.
  - `description: String`: A free text description for the project.
- Relationships:
  - `HAS_FIELD (Outgoing, 0..*)`: links to StudyProjectFields, for each study in the project.
  - `HOLDS_PROJECT (Incoming, 0..*)`: links to the Clinical Programme the project belongs to.

### StudyRoot / DeletedStudyRoot
- Description:  Root object for a single study definition. May have one or more linked versions. 
- Example: "Study_000001"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the study.
- Relationships:
  - `HAS_DRAFT (Outgoing, 1..*)`: a link to the different draft versions of the study.
  - `LATEST_DRAFT (Outgoing, 0..1)`: if the study is currently in a draft state, a link to that draft value.
  - `LATEST_RELEASED (Outgoing, 0..1)`: if the study is currently in a released state, a link to that released value.
  - `RELEASED (Outgoing, 0..1)`: if available, a link to the latest released version of the study.
  - `LATEST_LOCKED (Outgoing, 0..1)`:  if the study is currently in a locked state, a link to that locked value.
  - `DELETED (Outgoing, 0..1)`: if the study is currently deleted, a link to the deleted value.
  - `HAS_LOCKED (Outgoing, 0..*)`:  links to all the (previously) locked versions of the study.
  - `AUDIT_TRAIL (Outgoing, 1..*)`: relationships to every audit trail entry (StudyAction) for this study object.
  
### StudyValue
- Description:  A specific version of a study.
- Example: (A complete study definition, including fields and selections)
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the object.
- Relationships:
  - `HAS_PROJECT (Outgoing, 1)`: a link to the configured study project field for the study.
  - `HAS_FLOAT_FIELD (Outgoing, 0..*)`: links to all the Study Float Fields defined for the study.
  - `HAS_TEXT_FIELD (Outgoing, 0..*)`: links to all the Study Text Fields defined for the study.
  - `HAS_TIME_FIELD (Outgoing, 0..*)`: links to all the Study Time Fields defined for the study.
  - `HAS_BOOLEAN_FIELD (Outgoing, 0..*)`: links to all the Study Boolean Fields defined for the study.
  - `HAS_ARRAY_FIELD (Outgoing, 0..*)`: links to all the Study Array Fields defined for the study.
  - `HAS_STUDY_OBJECTIVE (Outgoing, 0..*)`: links to all the Study Objectives defined for the study.
  - `HAS_STUDY_ENDPOINT (Outgoing, 0..*)`: links to all the Study Endpoints defined for the study.
  - `HAS_STUDY_COMPOUND (Outgoing, 0..*)`: links to all the Study Compounds defined for the study.
  - `HAS_STUDY_EPOCH (Outgoing, 0..*)`: links to all the Study Epochs defined for the study.
  - `HAS_STUDY_VISIT (Outgoing, 0..*)`: links to all the Study Visits defined for the study.
  - `HAS_STUDY_ASSESSMENT (Outgoing, 0..*)`: links to all the Study Assessments defined for the study.
  - `HAS_DRAFT (Incoming, 1)`: if the study value is a draft, a relationship to the study root.
  - `LATEST_DRAFT (Incoming, 1)`: if the study value is the latest draft, a relationship to the study root.
  - `LATEST_RELEASED (Incoming, 1)`: if the study value is the latest release, a relationship to the study root.
  - `RELEASED (Incoming, 1)`: if the study value is a release, a relationship to the study root.
  - `LATEST_LOCKED (Incoming, 1)`: if the study value is the latest locked version, a relationship to the study root.
  - `DELETED (Incoming, 1)`: if the study value is a deleted version, a relationship to the study root.
  - `HAS_LOCKED (Incoming, 1)`: if the study value is a locked version, a relationship to the study root.
  - `BEFORE (Incoming, 0..1)`: a link to the study action that updated the study value.
  - `AFTER (Incoming, 1)`: a link to the study action that created the study value.
  
### StudyField (StudyProjectField / StudyFloatField / StudyTextField / StudyTimeField / StudyBooleanField / StudyArrayField)
- Description:  A (key, value) pair representing a field that is added to a study definition.
- Example: ("planned study length", "10 days")
- Properties: 
  - `name: String (Required, Unique)`: The name of the field (a dictionary key).
  - `value: String`: The value of the field (a dictionary value).
- Relationships:
  - `HAS_REASON_FOR_NULL_VALUE (Outgoing, 0..1)`: link to a control terminology term to be used as a null value.
  - `HAS_TYPE (Outgoing, 1)`: link to a control terminology term to be used as a type.
  - `HAS_FIELD_UNIT (Outgoing, 0..1)`: link to a control terminology term to be used as a unit.
  - `HAS_PROJECT (Incoming, 1)`: (for a StudyProjectField), the study value that uses the field.
  - `HAS_FLOAT_FIELD (Incoming, 0..*)`: (for a StudyFloatField), the study value that uses the field.
  - `HAS_TEXT_FIELD (Incoming, 0..*)`: (for a StudyTextField), the study value that uses the field.
  - `HAS_TIME_FIELD (Incoming, 0..*)`: (for a StudyTimeField), the study value that uses the field.
  - `HAS_BOOLEAN_FIELD (Incoming, 0..*)`: (for a StudyBooleanField), the study value that uses the field.
  - `HAS_ARRAY_FIELD (Incoming, 0..*)`: (for a StudyArrayField), the study value that uses the field.
  - `BEFORE (Incoming, 0..1)`: a link to the study action that updated the field.
  - `AFTER (Incoming, 1)`: a link to the study action that created this field.
  
  
### StudySelection
- Description:  A study selection represents a complex object (more than a simple field) selected as part of a study. This can be a library element, or a concept.
- Also has another label, e.g. StudyObjective or StudyEndpoint
- Example: "StudySelection_000001" (abstract)
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the selection.
- Relationships:
  - `BEFORE (Incoming, 0..1)`: a link to the study action that modified the selection.
  - `AFTER (Incoming, 0..1)`: a link to the study action that created the selection.

### OrderedStudySelection
- Description:  An ordered study selection extends a basic selection with an order property.
- Example: "OrderedStudySelection_000001" (abstract)
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the object.
  - `order: Integer (Required)`: The order of the selection inside the study.
  - `accepted_version: Boolean (Required)`: Whether the selection was approved.
- Relationships:
  - `BEFORE (Incoming, 0..1)`: a link to the study action that modified the selection.
  - `AFTER (Incoming, 0..1)`: a link to the study action that created the selection.

### StudyObjective (also see StudySelection)
- Description:  A study objective provides a way to link studies to objectives as defined from a template.
- Example: "StudyObjective_000001"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the object.
  - `order: Integer (Required)`: The order of the selection inside the study.
  - `accepted_version: Boolean (Required)`: Whether the selection was approved.
- Relationships:
  - `HAS_OBJECTIVE_LEVEL (Outgoing, 0..1)`: a link to the control terminology that represents the objective level.
  - `HAS_SELECTED_OBJECTIVE (Outgoing, 0..1)`: a link to the objective library object that is selected.
  - `HAS_STUDY_OBJECTIVE (Incoming, 1)`: a link to the study value that uses this selection.
  - `STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE (Incoming, 0..*)`: links to all the study endpoints that belong to this study objective.
  - `BEFORE (Incoming, 0..1)`: a link to the study action that modified the selection.
  - `AFTER (Incoming, 0..1)`: a link to the study action that created the selection.

  
### StudyEndpoint (also see StudySelection)
- Description:  A study endpoint provides a way to link studies to endpoints as defined from a template.
- Example: "StudyEndpoint_000001"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the object.
  - `order: Integer (Required)`: The order of the selection inside the study.
  - `accepted_version: Boolean (Required)`: Whether the selection was approved.
- Relationships:
  - `HAS_SELECTED_ENDPOINT (Outgoing, 0..1)`: a link to the endpoint library object that is selected.
  - `HAS_SELECTED_TIMEFRAME (Outgoing, 0..1)`: a link to the timeframe library object that is selected.
  - `HAS_ENDPOINT_LEVEL (Outgoing, 0..1)`: a link to the control terminology that represents the objective level.
  - `HAS_UNIT (Outgoing, 0..1)`: a link to the unit definition value for the selected endpoint.
  - `STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE (Outgoing, 0..1)`: a link to a study objective that this endpoint belongs to.
  - `HAS_STUDY_ENDPOINT (Incoming, 1)`: a link to the study value that uses this selection.
  - `BEFORE (Incoming, 0..1)`: a link to the study action that modified the selection.
  - `AFTER (Incoming, 0..1)`: a link to the study action that created the selection.

### StudyCompound
- Description:  A study compound provides a way to link studies to compound as defined in control terminology.
- Example: "StudyCompound_000001"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the selected compound.
  - `order: Integer (Required)`: The order of the selection inside the study.
  - `accepted_version: Boolean (Required)`: Whether the selection was approved.
  - `notes: String`: Free-text notes that can be added to the compound selection.
- Relationships:
  - `HAS_TYPE_OF_TREATMENT (Outgoing, 0..1)`: a link to control terminology for the type of treatment.
  - `HAS_ROUTE_OF_ADMINISTRATION (Outgoing, 0..1)`: a link to control terminology for the route of administration.
  - `HAS_DOSAGE_FORM (Outgoing, 0..1)`: a link to control terminology for the dosage form.
  - `IS_DISPENSED_IN (Outgoing, 0..1)`: a link to control terminology for the dispensing method.
  - `HAS_DEVICE (Outgoing, 0..1)`: a link to control terminology for the device.
  - `HAS_FORMULATION (Outgoing, 0..1)`: a link to control terminology for the formulation.
  - `HAS_REASON_FOR_MISSING (Outgoing, 0..1)`: a link to control terminology for the reason for missing.
  - `HAS_SELECTED_TIMEPOINT_PARAMETER (Outgoing, 0..1)`: a link to a template parameter to use as a timepoint.
  - `HAS_STUDY_COMPOUND (Incoming, 1)`: a link to the study that has this selected compound.
  

### StudyEpoch
- Description:  A study epoch represents a period of time in the context of a study.
- Example: `"Week 34-36"`
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the object.
  - `name: String`: a user-defined name for the period in the study context.
  - `short_name: String`: a short (abbreviated) name in the study context.
  - `description: String`: a textual description of the epoch.
  - `start_description: String`: A description of the timepoint when the epoch starts.
  - `end_description: String`: A description of the timepoint when the epoch ends.
  - `class: String`: The class (type) of study epoch.
- Relationships:
  - `HAS_TYPE (Outgoing, 1)`: link to control terminology that represents the epoch type.
  - `HAS_SUB_TYPE (Outgoing, 1)`: link to control terminology that represents the epoch sub type.
  - `HAS_EPOCH (Outgoing, 1)`: link to control terminology that represents the epoch.
  - `HAS_DURATION_UNIT (Outgoing, 1)`: a link to the unit for the epoch.
  - `STUDY_VISIT_HAS_STUDY_EPOCH (Incoming, 0..*)`: links to all the visits using an epoch.
  - `HAS_STUDY_EPOCH (Incoming, 1)`: a link to the study that contains the epoch. 
  

### StudyVisit
- Description:  a (patient) visit taking place as part of a study.
- Example: "Visit #2"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the object.
  - `legacy_visit_id (Unique): String`: legacy identifier for a visit.
  - `legacy_visit_type_alias: String`: legacy alias for the type of visit.
  - `legacy_name: String`: legacy name for the visit.
  - `legacy_sub_name: String`: legacy sub-name (description) for the visit.
  - `visit_number: Integer`: the number of the visit, in the chain of all study visits.
  - `visit_name_label: String`: abel for the visit (the type of visit)
  - `visit_sub_label: String`: sub-label for the visit (the sub-type of visit)
  - `short_visit_label: String`: Acronym/shorthand notation for the visit label.
  - `unique_visit_number: String`: optionally, a globally unique visit number.
  - `consecutive_visit_group: String`: group of the visit in the sequence.
  - `show_visit: Boolean`: Whether to show the visit as part of the study.
  - `visit_window_min: Integer`: minimum duration of the visit.
  - `visit_window_max: Integer`: maximum duration of the visit.
  - `description: String`: long, textual description of the visit.
  - `start_rule: String`: the condition for when the visit starts.
  - `end_rule: String`: the condition for when the visit ends.
  - `note: String`: optional, textual note for the visit.
- Relationships:
  - `STUDY_VISIT_HAS_STUDY_EPOCH (Outgoing, 1)`: link to the epoch the visit is in.
  - `HAS_VISIT_TYPE (Outgoing, 1)`: link to control terminology for the visit type.
  - `HAS_WINDOW_UNIT (Outgoing, 1)`: the unit for the visit window (duration).
  - `HAS_SELECTED_COMPOUND_PARAMETER (Outgoing, 1)`: which compound is involved in the visit.
  - `HAS_STUDY_VISIT (Incoming, 1)`: link to the study that the visit is part of.
  - `STUDY_ASSESSMENT_HAS_STUDY_VISIT (Incoming, 0..*)`: links to the assessment as part of the visit.
  
### StudyAssessment
- Description:  an assessment as part of a study. Assessments are parts of study visits.
- Example: "Assessment_000003"
- Properties: 
  - `uid: String (Required, Unique)`: An unique uid (identifier) for the object.
  - `order: Integer (Required)`: The order of the assessment inside the study.
  - `accepted_version: Boolean (Required)`: Whether the assessment was approved.
- Relationships:
  - `STUDY_ASSESSMENT_HAS_STUDY_VISIT (Outgoing, 1)`: link to the visit that the assessment is part of.
  - `HAS_ASSESSMENT (Outgoing, 1)`: link to the control terminology for the type of assessment.
  - `HAS_ASSESSMENT_INSTANCE (Outgoing, 1)`: link to the assessment library object in the MDR.
  - `HAS_STUDY_ASSESSMENT (Incoming, 1)`: link to the study this assessment is part of.
  

### StudyAction (one of Release, Delete, Lock, Unlock, Clone, Create, Edit)
- Description:  a study action represents an edit/state change of a study object.
- Example: "Study Edit at 2021/8/6 15:00"
- Properties: 
  - `date: String (Required, Unique)`: The date when the study was modified.
  - `status: String`: An optional status message describing the change.
  - `author_id: String (Required)`: The user that made the edit to the study.
- Relationships:
  - `BEFORE (Outgoing, 0..*)`: links to all elements that were part of the study before the action took place.
  - `AFTER (Outgoing, 0..*)`:  links to all elements that are part of the study after the action took place.
  - `AUDIT_TRAIL (Incoming, 1)`: the study root that this action belongs to.
  

## Relationship Types
### HOLDS_PROJECT
- Description: connections between a clinical programme, and the projects it contains.
- Examples: `"CP_001"` contains projects `["PRJ_001", "PRJ_002"]` (unversioned).
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `ClinicalProgramme`
- End nodes: `Project`

### HAS_FIELD
- Description: link between a project instance, and the project used as a study field.
- Examples: `PRJ_001` is used in studies `STD_001`, and `STD_002`. (versioned)
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `Project`
- End nodes: `StudyProjectField`


### HAS_DRAFT
- Description: links to all draft versions of a study.
- Examples: `Study_000001` has draft versions `0.1` and `0.2`.
- Properties:
  - (none)
- Cardinality: `(1..*)`
- Start nodes: `StudyRoot`
- End nodes: `StudyValue`

### LATEST_DRAFT
- Description: a link to the latest draft of the study, if the study is in a draft state.
- Examples: `Study_000001` has latest draft version `0.2`.
- Properties:
  - (none)
- Cardinality: `(0..1)`
- Start nodes: `StudyRoot`
- End nodes: `StudyValue`

### LATEST_RELEASED
- Description: a link to the latest study release, if the study is currently released.
- Examples: `Study_000001` has current version `1.0`.
- Properties:
  - (none)
- Cardinality: `(0..1)`
- Start nodes: `StudyRoot`
- End nodes: `StudyValue`

### RELEASED
- Description: a link to the latest study release, regardless of the current study state.
- Examples: `Study_000001` has current version `1.1`, but existing release `1.0`.
- Properties:
  - (none)
- Cardinality: `(0..1)`
- Start nodes: `StudyRoot`
- End nodes: `StudyValue`

### LATEST_LOCKED
- Description: if the study is locked, a link to that locked version.
- Examples: `Study_000001` is in locked version `1.2`.
- Properties:
  - (none)
- Cardinality: `(0..1)`
- Start nodes: `StudyRoot`
- End nodes: `StudyValue`

### DELETED
- Description: if the study is deleted, a link to that deleted version.
- Examples: `Study_000001` is in deleted version `1.3`.
- Properties:
  - (none)
- Cardinality: `(0..1)`
- Start nodes: `StudyRoot`
- End nodes: `StudyValue`

### HAS_LOCKED
- Description: links to all previously locked versions of a study.
- Examples:  `Study_000001` has old locked versions `1.2` and `1.4`.
- Properties:
  - `versionNumber: String (Required, Unique)`: the number for the locked version.
  - `versionDescription: String (Required)`: a textual description of the locked state.
- Cardinality: `(0..*)`
- Start nodes: `StudyRoot`
- End nodes: `StudyValue`

### HAS_STUDY_OBJECTIVE
- Description: for a study value (version), links to all objective selections.
- Examples: Study version 0.1 has study selections (StudyObjective_000001, StudyObjective_000002)
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyObjective`

### HAS_STUDY_ENDPOINT
- Description: for a study value (version), links to all endpoint selections.
- Examples: Study version 0.1 has study selections (StudyEndpoint_000001, StudyEndpoint_000002)
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyEndpoint`


### HAS_STUDY_COMPOUND
- Description: for a study value (version), links to all compound selections.
- Examples: Study version 0.1 has study selections (StudyCompound_000001, StudyCompound_000002)
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyCompound`


### HAS_STUDY_EPOCH
- Description: for a study value (version), links to all epoch selections.
- Examples: Study version 0.1 has study selections (StudyEpoch_000001, StudyEpoch_000002)
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyEpoch`

### HAS_STUDY_VISIT
- Description: for a study value (version), links to all visit selections.
- Examples: Study version 0.1 has study selections (StudyVisit_000001, StudyVisit_000002)
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyVisit`

### HAS_STUDY_ASSESSMENT
- Description: for a study value (version), links to all assessment selections.
- Examples: Study version 0.1 has study selections (StudyAssessment_000001, StudyAssessment_000002)
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyAssessment`
- 
### HAS_PROJECT
- Description: for a study value (version), a link to the project field that determines the project the study is in.
- Examples: `Study_000001` at version 0.1 is in project `PRJ_001`.
- Properties:
  - (none)
- Cardinality: `(0..1)`
- Start nodes: `StudyValue`
- End nodes: `StudyProjectField`

### HAS_FLOAT_FIELD
- Description: for a study value (version), links to all the study fields of type float.
- Examples: `Study_000001` at version 0.1 has float fields `{a: 1.0, b: 2.5}`.
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyFloatField`

### HAS_TEXT_FIELD
- Description: for a study value (version), links to all the study fields of type string.
- Examples: `Study_000001` at version 0.1 has string fields `{a: "abc", b: "def"}`.
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyTextField`

### HAS_TIME_FIELD
- Description: for a study value (version), links to all the study fields of type datetime.
- Examples: `Study_000001` at version 0.1 has time fields `{a: "2021-05-05 08:00", b: "2021-07-05 09:00"}`.
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyTimeField`

### HAS_BOOLEAN_FIELD
- Description: for a study value (version), links to all the study fields of type boolean.
- Examples: `Study_000001` at version 0.1 has time fields `{a: true, b: false}`.
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyBooleanField`

### HAS_ARRAY_FIELD
- Description: for a study value (version), links to all the study fields of type array.
- Examples: `Study_000001` at version 0.1 has array fields `{a: [1,2], b: ["q","w","e"]}`.
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyValue`
- End nodes: `StudyArrayField`

### HAS_REASON_FOR_NULL_VALUE / HAS_TYPE / HAS_FIELD_UNIT
- Description: Relationships from study fields to control terminology terms. Terms are selected from codelists based on configuration settings.
- Examples: StudyField `(Age, 25)` has type `Patient Age`, unit `years` and reason for null value `not specified`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyField`
- End nodes: `CTTermRoot`

### HAS_OBJECTIVE_LEVEL
- Description: Relationship from the study objective to its level as defined in control terminology.
- Examples: StudyObjective_000001 has level `Primary`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyObjective`
- End nodes: `CTTermRoot`

### HAS_SELECTED_OBJECTIVE
- Description: Relationship from the StudyObjective (Selection) to the objective library item.
- Examples: `StudyObjective_000001` uses library item `Objective_000005`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyObjective`
- End nodes: `ObjectiveValue`

### HAS_UNIT
- Description: A study endpoint has a selected unit (concept).
- Examples: `StudyEndpoint_000001` has unit definition `mg/ml`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyEndpoint`
- End nodes: `UnitDefinitionValue`

### HAS_ENDPOINT_LEVEL
- Description: Relationship from the study endpoint to its level as defined in control terminology.
- Examples: `StudyEndpoint_000001` has level `Secondary`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyEndpoint`
- End nodes: `CTTermRoot`
 
### HAS_SELECTED_ENDPOINT
- Description: Relationship from the StudyEndpoint (Selection) to the endpoint library item.
- Examples: `StudyEndpoint_000001` uses library item `Endpoint_000005`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyEndpoint`
- End nodes: `EndpointValue`

### HAS_SELECTED_TIMEFRAME
- Description: Relationship from the StudyEndpoint (Selection) to the timeframe library item.
- Examples: `StudyEndpoint_000001` uses library item `Timeframe_000005`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyEndpoint`
- End nodes: `TimeFrameValue`

### STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE
- Description: Links between two study selections (objectives and endpoints), indicating that they belong together in the study context.
- Examples: `StudyEndpoint_000001` belongs together with `StudyObjective_000001`.
- Properties:
  - (none)
- Cardinality: `(0..1)`
- Start nodes: `StudyEndpoint`
- End nodes: `StudyObjective`

### HAS_TYPE_OF_TREATMENT / HAS_ROUTE_OF_ADMINISTRATION / HAS_DOSAGE_FORM / IS_DISPENSED_IN / HAS_DEVICE / HAS_FORMULATION / HAS_REASON_FOR_MISSING
- Description: links from study compound selections to control terminology.
- Examples: `StudyCompound_000001` has type of treatment `XYZ`, route of administration `ABC`, ...
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyCompound`
- End nodes: `CTTermRoot`

### HAS_SELECTED_COMPOUND_PARAMETER
- Description: link from a study compound selection to a template parameter that it uses.
- Examples: `StudyCompound_000001` uses template parameter `Compound_ABC`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyCompound`
- End nodes: `TemplateParameterValueRoot`

### HAS_TYPE / HAS_SUB_TYPE / HAS_EPOCH
- Description: Relationships from study epoch selections to control terminology.
- Examples: `StudyEpoch_000001` has type `X`, subtype `X1`, and uses CT epoch `ABC`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyEpoch`
- End nodes: `CTTermRoot`

### HAS_DURATION_UNIT
- Description: Relationship from a study epoch selection to the unit it uses.
- Examples: `StudyEpoch_000001` has unit `days`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyEpoch`
- End nodes: `UnitDefinitionValue`

### HAS_VISIT_TYPE
- Description: Relationship from a study visit selection to control terminology defining the visit type. 
- Examples: `StudyVisit_000001` has type `Initial visit`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyVisit`
- End nodes: `CTTermRoot`

### HAS_WINDOW_UNIT
- Description: Relationship from a study visit selection to the unit it uses.
- Examples: `StudyVisit_000001` has unit `hours`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyVisit`
- End nodes: `UnitDefinitionValue`

### HAS_SELECTED_TIMEPOINT_PARAMETER
- Description: For a visit selection, which parameter to be used as a timepoint. 
- Examples: `StudyVisit_000001` uses template parameter `Timepoint_000001`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyVisit`
- End nodes: `TemplateParameterValue`

### STUDY_VISIT_HAS_STUDY_EPOCH
- Description: Links between two study selections (visits and epochs), indicating that they belong together in the study context.
- Examples: `StudyVisit_000001` belongs together with `StudyEpoch_000001`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyVisit`
- End nodes: `StudyEpoch`

### HAS_ASSESSMENT
- Description: Link from a study assessment selection to the specified control terminology as per configuration setting.
- Examples: `StudyAssessment_000001` uses control terminology assessment `ASSESS_01`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyAssessment`
- End nodes: `CTTermRoot`

### HAS_ASSESSMENT_INSTANCE
- Description: Link from a study assessment selection to an assessment concept as defined in the library.
- Examples: `StudyAssessment_000001` uses assessment concept `Assessment_000001`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyAssessment`
- End nodes: `AssessmentInstanceValue`

### STUDY_ASSESSMENT_HAS_STUDY_VISIT
- Description: Links between two study selections (assessments and visits), indicating that they belong together in the study context.
- Examples: `StudyAssessment_000001` belongs together with `StudyVisit_000001`.
- Properties:
  - (none)
- Cardinality: `(1)`
- Start nodes: `StudyAssessment`
- End nodes: `StudyVisit`

### AUDIT_TRAIL
- Description: relationships from a study root to all actions that were performed on the study, together forming the audit trail.
- Examples: `Study_000001` has actions `Create`, `Edit`, ...
- Properties:
  - (none)
- Cardinality: `(1..*)`
- Start nodes: `StudyRoot`
- End nodes: `StudyAction`

### BEFORE
- Description: relationship from a study action to parts of a study that were removed/modified during the action.
- Examples: `StudyAction_000001` removed selection `StudyObjective_000001`.
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyAction`
- End nodes: `StudyValue`, `StudyField`, `StudySelection`

### AFTER
- Description: relationship from a study action to parts of a study that were added/modified during the action.
- Examples: `StudyAction_000001` added selection `StudyObjective_000002`.
- Properties:
  - (none)
- Cardinality: `(0..*)`
- Start nodes: `StudyAction`
- End nodes: `StudyValue`, `StudyField`, `StudySelection`



