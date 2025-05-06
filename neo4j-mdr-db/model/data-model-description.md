# Clinical MDR Data Model

This document describes the data model for the Clinical MDR system. 

The initial purpose of the data model description is to support the design
and implementation process during the system development process of the
Clinical MDR system. But very importantly, the data model description needs
to support the usage and maintenance of the Clinical MDR system after go-live.
In this way the data model description is a very important part of the system documentation.

The scope and purpose of the Clinical MDR system is to support the clinical study
process from planning, study design, study specification, study set-up to drive
downstream automation.
Such a solution is deeply related to the data domain of clinical studies.
A Domain Driven Design is therefore very applicable for this type of IT solution,
and it fits well with an API based architecture where the API endpoints are closely
related to the data domain. The data model therefore plays a very important role for
the Clinical MDR system.

First step is to define the boundaries of the data domain the system should cover
by identifying the high-level data domains and subject areas these holds. This is
important for the scoping and identifying dependencies needed for the system components
as well as for project planning - both in the development phase and the following
maintenance phase.

Second step is to design the logical data model needed to solve the tasks and
deliverables for the system. This will also identify the data entities, attributes
and their relationships.

Final steps is to design how these data elements are to be exchanged via the system
interfaces (API’s) between the different system components, the domain data model.
Following this will be how the data model is to be implemented in the actual data storage,
the physical data model.

Below table gives an overview of the different types of data models, their definition
and purpose.

| Data Model Type | Definition | Purpose |
| --------------- | ---------- | ------- |
| **Conceptual Data Model** | A high-level description of informational needs underlying the design of a database | Define the scope for the data domain and subject areas the data model should cover |
| **Logical Data Model** | A data model of a specific problem domain expressed independently of a particular database management product or storage technology |Define the vocabulary for the main entities and attributes with their relationships. Typically made by each subject area. The language of the domain. |
| **Domain Data Model** | A domain model is a representation of the data, independent of the way the data is stored in the database | Define the way data can be exchanged between systems e.g. by an API based interface. Can be in various exchange formats like JSON, XML, CSV, etc. |
| **Physical Data Model** | A representation of a data design as implemented in a database management system | The technical specification for the design of the data base implementation |
******

## Conceptual Data Model – Domain Areas

Purpose of the domain areas in the conceptual data model is to define the overall data scope
for the Clinical MDR system. The system has the following data model domain areas that will
be described in the following sections:

![](./domain-areas.svg)


## Conceptual Data Model – Subject Areas

Purpose of the subject areas in the conceptual data model is to define the main data domains
and their main relationships. This is important to define the more detailed scope and for
identifying dependencies and use this insight for planning the implementation order for the
different components as well as dependencies when these are maintained later.

The conceptual data model diagram is layered by each data domain area and shows each subject
area with their main relationships.

![](./conceptual-model.svg)

A detailed description of the diagram is available here:
[conceptual-model-description.md](./conceptual-model-description.md)


## Logical Data Model

The logical data model defines the entities, their relationship and attributes of the data
domain independently on how these are implemented or exchanged.

As an example see below diagram for Objectives and Endpoints subject area – sub part of the
conceptual standards subject area. This is identical for both the Industry Standards and the
Sponsor Standards – depending on the relationship to the Library entity.

![](./logical-model-objectives-endpoints.svg)

A detailed description of the logical data model by each subject area is available here:
[logical-data-model-overview.md](./logical-data-model-overview.md)


## Domain Data Model

The domain data model represents the data model as the data is returned from the API calls.
The domain data model is made as an Object-Oriented class diagram representing the returned
result file from an API call. This can be represented in various exchange file formats like
JSON, XML, CSV, etc., but for the Clinical MDR system this will mainly be in JSON.
For some API endpoints other file formats will be supported, these can be used to support
exports into other systems.

As an example see below diagram for Objectives Templates data domain – sub part of the
conceptual standards subject area, corresponding to the /objective-templates API endpoint.
This is identical for both the Industry Standards and the Sponsor Standards – depending on
the relationship to the Library entity.

![TODO file is missing](./domain-model-objective-templates.svg)

A detailed description of the domain data model by each API endpoint, or data domain,
is available here: [domain-data-model-overview.md](./domain-data-model-overview.md)


## Physical Data Model

The physical data model represents the actual data model as it is implemented in the database.
For the Clinical MDR system the database is a Labeled Property Graph database (Neo4j). The
physical data model therefore describes the nodes and relationships with properties as
implemented in Neo4j.

As an example see below diagram for the ObjectivesTemplates nodes and relationships – sub part
of the conceptual standards subject area, corresponding to the `/objective-templates` API
endpoint. This is identical for both the Industry Standards and the Sponsor Standards –
depending on the relationship to the Library entity.

![TODO diagram is missing](//neo4j-model-objective-templates.svg)

One of the main design element in the physical Neo4j data model is the support full
versioning and audit trail capabilities. This is achieved by separating nodes that identify
data elements from the data element values, and capture all the data state attributes as
relationship properties between the identifier and value nodes. The identifier nodes will
have the 'Root' post fix in their name and the value nodes 'Value' as their name post fix.
All the state attributes as action, timestamps, user names, change description etc. will be
saved as part of relationship properties.

A detailed description of the physical Neo4j data model is available here:
[neo4j-data-model-overview.md](./neo4j-data-model-overview.md)


