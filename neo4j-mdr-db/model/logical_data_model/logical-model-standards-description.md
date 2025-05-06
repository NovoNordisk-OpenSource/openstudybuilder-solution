# Clinical MDR Logical Data Model for Industry and Sponsor Standards

This document describe the logical data model for the industry and sponsor defined data standards as well as references to diagrams and detailed descriptions by the individual subject areas of the logical data model.

The purpose of the logical data model is to define the vocabulary for the main entities and attributes with their relationships, being the langue of the domain used in the data modeling. The logical data model is grouped by subject areas, and as the subject areas for both the industry standards and the sponsor defined extensions share the same data structure these will be described together. We have defined the following subject areas that will be described in the following sections:

- Controlled Terminologies 
- Foundational Data Standards
- Conceptual Standards
- Therapeutic Area Standards
- Dictionaries


## Controlled Terminologies 
  The Controlled Terminologies subject area in the Industry Standards domain area holds the controlled terminologies as code lists and terms that are imported into the Clinical MDR. When these are imported a reference to the source library will be kept as well as reference to the external versioning information.

  The Sponsor Standards domain area holds the sponsor defined extensions to the industry standards as well as sponsor defined supplemental standards.

  ![Diagram: logical-model-controlled-terminologies.graphml](//logical-model-controlled-terminologies.graphml)

  A detailed description of the diagram is available here: ![Document: logical-model-descriptions-controlled-terminologi.md](//logical-model-descriptions-controlled-terminologi.md)

## Foundational Data Standards
  The Foundational Data Standards subject area in the Industry Standards domain area holds the clinical data standards and include models, domains and specifications for data representation. When these are imported into the Clinical MDR a reference to the source library will be kept as well as reference to the external versioning information.

  The Sponsor Defined Terminologies subject area holds extensions to standard terminologies, initially this will only be for CDISC Controlled Terminologies.

## Conceptual Standards
  The Conceptual Standards subject area holds the CDISC 360 Biomedical Concepts in form of Activities, Assessments and Analysis Concepts related to data derivation, analysis and analysis results.

  The Sponsor Defined Conceptual Standards subject area holds sponsor defined Biomedical Concepts in form of Activities, Assessments and Analysis Concepts related to data derivation, analysis and analysis results based on the CDISC 360 model.

## Therapeutic Area Standards
  The Therapeutic Area Standards subject area holds the definitions from the various CDISC Therapeutic Area User Guides (TAUG). These will reference the new CDISC conceptual standards, applied foundational standards as well as usage of controlled terminology.

  The Therapeutic Area and Project Standards subject area holds the sponsor defined definitions of Therapeutic Area as well as Project Specific selection of standards. These will reference the new CDISC conceptual standards, applied foundational standards as well as usage of controlled terminology. The can refer to what is required or optional to apply at the sponsor company.

## Dictionaries
  The Dictionaries subject area holds rich and highly specialised medical terminologies that facilitate sharing and exchange of clinical information. This can be e.g. LOINC, MedDRA, SNOMED etc.


