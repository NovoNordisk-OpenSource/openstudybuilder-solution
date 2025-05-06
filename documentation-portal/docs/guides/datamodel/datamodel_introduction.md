---
title: Introduction
date: 2021-06-06
---

# Introduction

The scope and purpose of the Clinial-MDR is to support the clinical study process from planning, study design, study specification, study set-up to drive downstream automation. Such a solution is deeply related to the data domain of clinical studies. A Domain Driven Design is therefore very applicable for this type of IT solution, and it fit well with an API based architecture where the API endpoints are closely related to the data domain. The data model therefore play a very important role for a Clinial-MDR system.

This section therefore describes the data model for the Clinial-MDR system component at different levels of abstraction each with a dedicated focus. The initial purpose of the data model description is to support the design and implementation process during the system development process of Clinial-MDR system. Equally important, the data model description needs to support the usage and maintenance of a Clinial-MDR system after go-live. The data model description is therefore an important outcome of the CDISC 360 PoC and  a very important part to share for the coming development of a CDISC 360 based Study MDR solution.

First step is to define the boundaries of the data domain the system should cover by identifying the high-level data domains and subject areas these holds. This is important for the scoping and identifying dependencies needed for the system components as well as for project planning - both in the development phase as well as the following maintenance phase.

Second step is to design the logical data model needed to solve the tasks and deliverables for the system. This will also identify the data entities, attributes and their relationships.

Final steps is to design how these data elements are to be exchanged via the system interfaces (API s) between the different system components, the domain data model. Following this will be how the data model is to be implemented in the actual data storage, the physical data model.

Below table gives an overview of the different types of data models, their definition and purpose:

| Data Model Type            | Definition                                                                          | Purpose                                                                            |
| -------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **[Conceptual Data Model](./conceptualmodel.md)**      | A high-level description of informational needs underlying the design of a database | Define the scope for the data domain and subject areas the data model should cover |
| **[Logical Data Model](./logicalmodel.md)**      | A high-level description of informational needs underlying the design of a database | Define the scope for the data domain and subject areas the data model should cover |
| **[Domain Data Model](./domainmodel.md)**      | A domain model is a representation of the data, independent of the way the data is stored in the database | Define the way data can be exchanged between systems e.g. by an API based interface. Can be in various exchange formats like JSON, XML, CSV, etc. |
| **[Physical Data Model](./physicalmodel.md)**      | A representation of a data design as implemented in a database management system | The technical specification for the design of the data base implementation |

