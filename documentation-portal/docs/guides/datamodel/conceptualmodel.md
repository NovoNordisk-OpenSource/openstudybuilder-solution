---
title: Conceptual Data Model
date: 2020-11-14
---

# Conceptual Data Model

This document describe the diagram for the Clinical MDR conceptual data model.

Purpose of the **conceptual data model** is to define the overall data model domain areas and the subject areas they contain. We have defined the following data model domain areas that will be described in the following sections:

- System Configuration
- Industry Standards
- Sponsor Standards
- Study Definitions
- Administrative Definitions

[![Conceptual Model](~@source/images/model/conceptual_data_model/conceptual-model.png)](../../images/model/conceptual_data_model/conceptual-model.png)


## System Configuration

The **System Configuration** domain area holds the various entities that form the system configuration, like the connected external and defined internal libraries.

- ### Library Definitions
  The **Library Definitions** subject area holds the definition of the library definitions defined in the system, like the external **CDISC Library** and internal Sponsor Library.


## Industry Standards

The **Industry Standards** domain area holds the imported industry standards like **CDISC Controlled Terminologies** and **Foundational Data Standards** like *SDTM*. Initially only from **CDISC Library**, but more will be added later like **LOINC**, **SNOMED** and **MedDRA** dictionaries.

- ### Controlled Terminologies 
  The **Controlled Terminologies** subject area in the Industry Standards domain area holds the controlled terminologies as code lists and terms that are imported into the Clinical MDR. When these are imported a reference to the source library will be kept as well as reference to the external versioning information.

- ### Foundational Data Standards
  The **Foundational Data Standards** subject area in the Industry Standards domain area holds the clinical data standards and include models, domains and specifications for data representation. When these are imported into the Clinical MDR a reference to the source library will be kept as well as reference to the external versioning information.

- ### Conceptual Standards
  The **Conceptual Standards** subject area holds the **CDISC 360 Biomedical Concepts** in form of *Activities, Assessments and Analysis Concepts* related to *data derivation, analysis and analysis results.*

- ### Therapeutic Area Standards
  The **Therapeutic Area Standards** subject area holds the definitions from the various **CDISC Therapeutic Area User Guides (TAUG)**. These will reference the new **CDISC Conceptual Standards**, applied foundational standards as well as usage of **Controlled terminology**.

- ### Dictionaries
  The **Dictionaries Subject Area** holds rich and highly specialised medical terminologies that facilitate sharing and exchange of clinical information. This can be e.g. LOINC, MedDRA, SNOMED etc.


## Sponsor Standards

- The **Sponsor Standards** domain area holds the sponsor defined extensions to the industry standards as well as sponsor defined supplemental standards.

- ### Sponsor Defined Terminologies
  The **Sponsor Defined Terminologies** subject area holds extensions to standard terminologies, initially this will only be for **CDISC Controlled Terminologies**.

- ### Sponsor Defined Data Standards Extensions
  The **Sponsor Defined Data Standards Extensions** subject area holds extensions and configuration to **Foundational Standards**. These are initially only for **CDISC Foundational Standards** that are designed so they can be extended. E.g. adding standard *SDTM variables to SDTM dataset domains or creating sponsor defined SDTM domains*.

- ### Sponsor Defined Conceptual Standards
  The **Sponsor Defined Conceptual Standards** subject area holds sponsor defined **Biomedical Concepts** in form of **Activities**, **Assessments** and **Analysis Concepts** related to **Data Derivation**, **Analysis and Analysis Results** based on the **CDISC 360** model.

- ### Therapeutic Area and Project Standards
  The **Therapeutic Area and Project Standards** subject area holds the sponsor defined definitions of **Therapeutic Area** as well as **Project Specific** selection of standards. These will reference the new **CDISC Conceptual Standards**, applied foundational standards as well as usage of controlled terminology. The can refer to what is required or optional to apply at the sponsor company.


## Study Definitions

- The Study Definitions domain area holds the study level metadata for the study definitions and specifications.

- ### Study Definitions
  The Study Definitions subject area holds the basic definition for a study in the form of the study identification, study title, phase, type and the selected data standard versions.

- ### Study Designs
  The Study Designs subject area holds the structural description of the study design in for of study arms, epochs, elements, visit schedules and planned interventions.

- ### Study Selections and Scheduling
  The Study Selections and Scheduling subject area holds the selection, configuration and scheduling of biomedical and analysis concepts for the study. E.g. schedule of activities and assessments.


## Administrative Definitions

- The Administrative Definitions domain area holds the system administrative definitions.

- ### Projects
  The Projects subject area holds the project definitions and the relationship to therapeutic area, investigational drugs and indications.

- ### Access Groups
  The Access Groups subject area holds the defined access groups that can be assigned to users.

- ### Users
  The Users subject area holds the users of the Clinical MDR system with their relationship to access groups and system roles.

- ### System Roles
  The System Roles subject area holds the defined system roles that can be assigned to users.

