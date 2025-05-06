# Integration Architecture

[![System Integrations](~@source/images/documentation/studybuilder-system-integrations-future.svg)](../../images/documentation/studybuilder-system-integrations-future.svg)


The system will have the following integrations.

| System <br> (Integration type) | Technology | Description |
| ---------- | ------ | ------------------ |
| CDISC Library <br> (External source data) | External restful API using access token for CDISC Library account connected to CDISC membership | CDISC Library holds all CDISC terminology and data exchange standards. <br> Possibility to import relevant standards, or all available standards, from the CDISC Library into the Clinical MDR so these can be referred to from sponsor standards as well as study specifications. <br> See more at https://www.cdisc.org/cdisc-library |
| Other sources <br> (File based source data) | Data exported from another StudyBuilder environment in JSON format; Or manual exports from external dictionaries with file creation in .csv format; Or manual file based dataset creation in .csv or JSON formats. | The import of dictionary terms from SNOMED, MED-RT, UNII and UCUM. <br> This will either be done by download of files from external dictionary sites (like for UCUM). Alternatively files are created from legacy systems (MED-RT and UNII) or files are created manually based on exported data with manual corrections (e.g. linking Unit Definitions to UCUM). |
| UNIX SCE & CDW <br> (Internal source data) | Data are extracted from the CDW MDR system using the MEDATA_VIEWER access profile from CDW directly or via UNIX SCE to CDW interface. | In this initial release a subset of sponsor defined standards from the General Clinical Metadata (GCMD) is migrated into the StudyBuilder system.  |
| Word add-in <br> (Internal target data) | Scripting (?) programs within the Microsoft Word connecting to the internal StudyBuilder MDR API | The NN Microsoft Word authoring tool is used for our Common Protocol Template (CPT), this NN CPT will include content controls and importing functionality from the Clinical MDR API populating the structured protocol content defined within the StudyBuilder system. |
| UNIX SCE <br> (Internal target data) | StudyBuilder internal restful API to the Clinical MDR using a system account access token (as UNIX SCE not is on NN Corp Active Directory).<br> Executed from SAS on UNIX SCE using the SAS HTTP procedure.<br> This is used to transfer terminology and data exchange standards as well as study specification metadata into the SCE environment to be used for CDISC SDTM and ADaM generation as well as other data standards related deliverables. | Currently only a few sample listings are made to test connection readning data from the Clinical MDR API into the UNIX SCE system |



