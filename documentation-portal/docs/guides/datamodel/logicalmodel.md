---
title: Logical Data Model
date: 2020-11-14
---

## For Library of Objectives and Endpoints

This document describe the entities in diagram: logical-model-objectives-endpoints.graphml.

[![Logical Data Model](~@source/images/model/logical_data_model/logical-model-objectives-endpoints.png)](../../images/model/logical_data_model/logical-model-objectives-endpoints.png)


The Objectives and Endpoints are part of the top levels of the conceptual standards that refer to Activities and Assessments. These can exist both as part of the CDISC 360 concept based standards as well as sponsor defined concept standards.

| Entity | Definition | Example |
| ------ | ---------- | -------- |
| Library                | Entity holds the name and definition of the library that are the source and owner for the elements in the library. | The CDISC Library and a specific sponsors library.  |
| ObjectiveTemplate      | A sentence syntax for an objective text including reference to parameters that can be replaced with standardized values. | To demonstrate superiority in the efficacy of [StudyIntervention] to [ComparatorIntervention] in [Assessment] |
| Objective              | A sentence that represent a specific objective sentence based on a template where the parameters are replaced with specific standardized values. | To demonstrate superiority in the efficacy of human insulin to Metformin in HbA1c |
| EndpointTemplate       | A sentence syntax for an endpoint text including reference to parameters that can be replaced with standardized values. | Mean Change from Baseline in [Assessment] after [Timeframe] ([Unit]) |
| TemplateParameter      | A sentence that represent a specific endpoint sentence based on a template where the parameters are replaced with specific standardized values. | Mean Change from Baseline in HbA1c after 26 weeks (%) |
| TemplateParameterValue | Hold the specific standardized values for template parameters. These are categorised by the specific types of template parameters. | human insulin (StudyIntervention), HbA1c (Assessment) |

## For Controlled Terminologies

This document describe the entities in diagram: logical-model-controlled-terminologies.graphml.

[![Logical Data Model](~@source/images/model/logical_data_model/logical-model-controlled-terminologies.png)](../../images/model/logical_data_model/logical-model-controlled-terminologies.png)

The controlled terminologies is a set of code lists and term values used with data items within CDISC-defined datasets. These can both be part of the industry standards as well as sponsor defined standards. When part of industry standards these are loaded form the CDISC Library. Some of the CDISC defined code lists is defined as extensible and in these a sponsor can define additional terms. A sponsor can also define code lists and terms in these.

| Entity | Definition | Example |
| ------ | ---------- | -------- |
| Library                | Entity holds the name and definition of the library that are the source and owner for the elements in the library. | The CDISC Library and a specific sponsors library.  |
| CTModel | The CDISC Controlled Terminologies are defined for the various CDISC foundational models data standard models (e.g. CDASH, SDTM, ADaM, etc.). The Terminology is versioned by release dates and for each release date a relationship exist to each code list or term being created, updated or deleted in that version. Each version of the terminology have a reference to a Terminology Package that acts as a container for all code lists and terms contained in a package. Most code lists and terms are unchanged between package versions. | Controlled Terminology for: Protocol Entities, SDTM, SEND, CDASH, and ADaM |
| CTPackage | The Controlled Terminology Package is a container for all of the valid code lists and term values for a terminology release | SDTM Controlled Terminology Package 38 Effective 2019-06-28 |
| CTCodeList | Controlled Terminology Code lists are defining the controlled terms that are used in a specific column of a CDISC foundational  data standard. A code list can be defined by CDISC, and can be defined as a non-extensible or extensible code list. The code lists applicable for a study will be documented as part of the Define.xml file for a dataset and this documentation will refer to this definition of the code list. | RACE (CDISC SDTM Race Terminology) |
| CTCodeListName | Holds the unique submission values (names) for the CTCodeLists | RACE |
| CTTerm | Controlled Terminology term values are defined as being part of an code list. The term values can be defined by CDISC or as a sponsor defined term. The individual term values applicable for a study will be documented as part of the Define.xml file for code list or for a value level definition. This documentation will refer to this definition of the term value. | BLACK OR AFRICAN AMERICAN (Black or African American) |
| CTTermName | Holds the unique submission values (names) for the CTTerm | BLACK OR AFRICAN AMERICAN |
| CTTermSynonym | Holds synonym values for the CTTermName values |   |

## Manage Study Definition

[![Logical Data Model](~@source/images/model/logical_data_model/logical-model-study-definition.png)](../../images/model/logical_data_model/logical-model-study-definition.png)

## Study Definition - Study Define Parameters

[![Logical Data Model](~@source/images/model/logical_data_model/logical-model-study-definition-parameters.png)](../../images/model/logical_data_model/logical-model-study-definition-parameters.png)


## Study Definition - Study Design

[![Logical Data Model](~@source/images/model/logical_data_model/logical-model-study-definition-design.png)](../../images/model/logical_data_model/logical-model-study-definition-design.png)

## Study Definition - Planned Objectives and Planned Endpoints

[![Logical Data Model](~@source/images/model/logical_data_model/logical-model-study-definition-objectives-endpoints.png)](../../images/model/logical_data_model/logical-model-study-definition-objectives-endpoints.png)


## For Study Management (DDD model)

This document describe the management of a Study in the Domain Design Driven approach.

[![Logical Data Model](~@source/images/model/logical_data_model/logical-ddd-model-manage-study.png)](../../images/model/logical_data_model/logical-ddd-model-manage-study.png)

## For Study Type (DDD model)

This document describe the Study Type of a Study in the Domain Design Driven approach.

[![Logical Data Model](~@source/images/model/logical_data_model/logical-ddd-model-study-type.png)](../../images/model/logical_data_model/logical-ddd-model-study-type.png)

## For Planned Objectives and Planned Endpoints in a Study (DDD model)

This document describe the Planned Objectives and the Planned Endpoints of a Study in the Domain Design Driven approach.

[![Logical Data Model](~@source/images/model/logical_data_model/logical-ddd-model-study-objectives-endpoints.png)](../../images/model/logical_data_model/logical-ddd-model-study-objectives-endpoints.png)

## For Planned Compounds in a Study (DDD model)

This document describe the Planned Compounds of a Study in the Domain Design Driven approach.

[![Logical Data Model](~@source/images/model/logical_data_model/logical-ddd-model-study-compounds.png)](../../images/model/logical_data_model/logical-ddd-model-study-compounds.png)

