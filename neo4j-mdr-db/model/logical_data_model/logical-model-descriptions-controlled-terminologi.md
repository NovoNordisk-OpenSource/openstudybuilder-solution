# Desription of Logical Data Model for Controlled Terminologies

This document describe the entities in diagram: logical-model-controlled-terminologies.graphml.

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


