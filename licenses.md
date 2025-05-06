# Licenses used within the OpenStudyBuilder ecosystem

The following is a assessment on the ability to combine the imbedded dependencies into a larger piece of work and then release under the license GPLv3.  
The assessment below has only accounted for the copy-left licenses as well as licenses that may be difficult to combine with the GPLv3.  
For a preemptive list of all licenses consumed within each sub-component please refer to their respective Software Bill of Materials.

## OpenStudyBuilder App

| Package | License | Can be combined |
|---|---|-|
| big-integer-1.6.52.tgz | The Unlicense (Public Domain) | OK |
| jszip-3.10.1.tgz | Dual-licensed as MIT or GPL | OK |

The usage of the Unlicense, which acts as Public Domain poses no issue as it can be viewed as the absolute most permissive license available.
The dual-licensing of `jszip` allows for using MIT license which is preferred due to the permissive nature of this license.
**Conclusion**  
The OpenStudyBuilder App frontend can be released under GPLv3 License.


## Clinical MDR API

| Package | License | Can be combined |
|---|---|-|
| certifi (2025.1.31) | MPL v. 2.0 | OK |
| hypothesis (6.115.6) | MPL v. 2.0 | OK |
| pyphen (0.17.2) | GPL 2.0+/LGPL 2.1+/MPL 1.1 tri-license | OK |
| typing_extensions (4.12.2) | Python License | OK |
| usdm (0.59.0) | GPL 3.0 | OK |
| yattag (1.16.1) | LGPL 3.0 | OK |

As the licenses consumed within the Clinical MDR API is using MPL version 2.0 it is assessed that it poses no issue to release in combination with GPL and GPL derivatives since version 2.0 of the MPL license was rewritten to allow for combination with the GPL versions as well as derivatives of GPL.  
The Python Software Foundation License, also referred to as the PSFL, is a permissive license and can be combined with sub-components that are licensed under GPL and GPL derivatives. The GPL 2.0+ includes also all higher GPL version, for this also GPLv3. GPLv3 is compatible with GPLv3.
**Conclusion**  
The Clinical MDR API can be released under GPLv3 License.


## Documentation Portal

The documentation portal does not contain any production packages.
**Conclusion**  
The Documentation Portal can be released under GPLv3 License.

## Neo4j MDR DB

| Package | License | Can be combined |
|---|---|-|
| certifi 2024.8.30 | MPL v. 2.0 | OK |

As the licenses is using MPL version 2.0 it is assessed that it poses no issue to release in combination with GPL and GPL derivatives since version 2.0 of the MPL license was rewritten to allow for combination with the GPL versions as well as derivatives of GPL. 
**Conclusion**  
The Neo4j MDR DB can be released under GPLv3 License.

## MDR Standards Import

| Package | License | Can be combined |
|---|---|-|
| certifi 2024.12.14 | MPL v. 2.0 | OK |
| packaging 24.2 | Dual-licensed as BSD-2-Clause or Apache-2.0 | OK |

As the licenses is using MPL version 2.0 it is assessed that it poses no issue to release in combination with GPL and GPL derivatives since version 2.0 of the MPL license was rewritten to allow for combination with the GPL versions as well as derivatives of GPL. 
The `packaging` has the possibility for dual-licensing, where Apache-2.0 is preferrable.
**Conclusion**  
The MDR Standards Import can be released under GPLv3 License.

## StudyBuilder Import

| Package | License | Can be combined |
|---|---|-|
| certifi 2024.8.30 | MPL v. 2.0 | OK |

As the licenses is using MPL version 2.0 it is assessed that it poses no issue to release in combination with GPL and GPL derivatives since version 2.0 of the MPL license was rewritten to allow for combination with the GPL versions as well as derivatives of GPL. 
**Conclusion**  
The Data Import can be released under GPLv3 License.

## StudyBuilder Export

| Package | License | Can be combined |
|---|---|-|
| certifi 2025.1.31 | MPL v. 2.0 | OK |

As the licenses is using MPL version 2.0 it is assessed that it poses no issue to release in combination with GPL and GPL derivatives since version 2.0 of the MPL license was rewritten to allow for combination with the GPL versions as well as derivatives of GPL.
**Conclusion**  
The StudyBuilder Export can be released under GPLv3 License.

## DB Schema Migration

| Package | License | Can be combined |
|---|---|-|
| certifi 2024.12.14 | MPL v. 2.0 | OK |

As the licenses is using MPL version 2.0 it is assessed that it poses no issue to release in combination with GPL and GPL derivatives since version 2.0 of the MPL license was rewritten to allow for combination with the GPL versions as well as derivatives of GPL.
**Conclusion**  
The DB Schema Migration can be released under GPLv3 License.

## System-Tests - UI-Tests

| Package | License | Can be combined |
|---|---|-|
| cypress-drag-drop (2.3.0) | GPL 3.0 | OK |

GPLv3 is compatible with GPLv3.
**Conclusion**  
The System-Tests - UI-Tests can be released under GPLv3 License.


## Overall conclusion

Even though the aggregate of combining all three products as a single deliverable which is then either distributed in machine readable source code through Source Code Management systems such as Gitlab or Github or as packaged pre-compiled binaries, the project has assessed that they adhere to the license requirements due to the fact that  
1. The source code is readily available in a machine readable format as required by the GPL licenses
1. The distribution of the software, either through pre-compiled binaries, as a web platform that can be reached by public www or as readable source code is accompanied with a clear overview of the used libraries and their respective license descriptions or with links to the license descriptions
It is determined to be in the best interest of the project to release the above mentioned products of the aggregate solution under the following license model  

| Product | Product Description | Product License |
|--|------|--|
| OpenStudyBuilder | JavaScript based web application with the UI for creating the study definition specification, maintaining library standards. The OpenStudyBuilder app holds two main modules: Library and Studies | GPLv3 |
| Clinical MDR API | Python based web application based on FAST API framework supporting all CRUD actions to the database, access control, versioning, workflows and data integrity rules. | GPLv3 |
| Documentation Portal | Markdown based documentation portal with OpenStudyBuilder Introduction, User Guides, System Documentation, Data Models and more. | GPLv3 |
| Neo4j MDR DB | Python tools for Neo4j MDR DB. | GPLv3 |
| MDR Standards Import | Python tools for import of standards. | GPLv3 |
| StudyBuilder Import | Python tools for data imports. | GPLv3 |
| StudyBuilder Export | Python tools for data exports. | GPLv3 |
| DB Schema Migration | Python tool for schema migration. | GPLv3 |
| System-Tests - UI-Tests | Gherkin End-to-end tests | GPLv3 |

The goal of the project is to ensure collaboration within the community on a set standard of defining the mapping tables between documents used in Clinical Studies within developing medicine and the project has collaborated with [COSA](https://www.cdisc.org/cosa) from [CDISC](https://www.cdisc.org/about). It is deemed to be in the best interest of Novo Nordisk, as well as the broader community doing Clinical Studies, that an alignment on data standards are in place, which is what the project hopes to achieve by the current project and which is also why it has been decided to be beneficial to Open Source the code in the hopes of a community driven approach to standardise on the mapping of data standards.  

**Final remarks**  
The above assessment has been conducted in a collaboration between an open source advisor consultancy and Novo Nordisk security/open source personnel. For any enquiry about the assessment please direct you questions to `openstudybuilder@gmail.com`.

