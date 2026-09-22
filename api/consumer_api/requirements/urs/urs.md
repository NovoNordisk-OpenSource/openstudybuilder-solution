# Overview

This document contains a set of user requirements related to OpenStudyBuilder Consumer API.

# URS-ConsumerApi-Library-Activities

Consumers must be able to retrieve a list of all library activities and activity instances via the Consumer API.

# URS-ConsumerApi-Library-ControlledTerminology

Consumers must be able to retrieve controlled terminology from the library via the Consumer API, including CT codelists and codelist terms.

# URS-ConsumerApi-Library-UnitDefinitions

Consumers must be able to retrieve a list of unit definitions for a specified unit subset from the library via the Consumer API.

# URS-ConsumerApi-Projects

Consumers must be able to retrieve a list of all projects that exist in OpenStudyBuilder via the Consumer API, including the clinical programme each project belongs to.

The list must expose the project IDs accepted when creating a study, so that a consumer can discover valid values without leaving the Consumer API.

# URS-ConsumerApi-Studies

Consumers must be able to retrieve a list of all studies that exist in OpenStudyBuilder via the Consumer API.

# URS-ConsumerApi-Studies-Create

Consumers with write access must be able to create a new top-level study definition via the Consumer API by providing a study number and/or a study acronym, together with the ID of an existing project.

The API must reject requests that identify a non-existent project, that provide neither a study number nor a study acronym, or that would result in a duplicate study number or a duplicate study acronym already used by another study.
Creating study subparts is out of scope for the Consumer API.

# URS-ConsumerApi-Studies-SoA

Consumers must be able to retrieve the following entities related to Schedule of Activities via the Consumer API:

- Study Visits
- Study Activities
- Study Activity Instances
- Detailed SoA
- Operational SoA

# URS-ConsumerApi-Studies-SoA-Create

Consumers with write access must be able to create or replace a study Schedule of Activities via the Consumer API by submitting a complete SoA payload containing epochs, visits and activities.

The API must validate references and controlled terminology in the submitted payload and reject invalid or inconsistent requests.

# URS-ConsumerApi-Studies-Papillons

Consumers must be able to retrieve the following entities related to Schedule of Activities via the Consumer API, in a format suitable for SDTM generation:

- Detailed SoA
- Operational SoA

# URS-ConsumerApi-Library-Papillons-NonStandardVariables

Consumers must be able to retrieve Non-Standard Variables via the Consumer API, in a format suitable for MMA SDTM_QNAM import.

Consumers must also be able to resolve a single SEMTCDT (Semantic Data Type) term to its NSVXMLDT (NSV XML Data Type) equivalent.

# URS-ConsumerApi-Studies-AuditTrail

Consumers must be able to retrieve audit trail information for studies via the Consumer API.

The audit trail must include information about actions performed on study entities, including:

- Timestamp of the action
- Study Id
- Action type (Create, Edit, Delete)
- Entity affected by the action
- Properties that were changed
- Anonymized information about the user who performed the action

The audit trail must protect user privacy by anonymizing user identifiers.
