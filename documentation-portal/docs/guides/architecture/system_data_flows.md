# System Data Flows

[![System Integrations](~@source/images/documentation/studybuilder-system-dataflow.svg)](../../images/documentation/studybuilder-system-dataflow.svg)

The system supports the following data flows.

| User / Agent | Data Flow |
| ------- | ---------------|
| Standards Developer | Standards Developer can download, impact assess and import data standards from CDISC Library into the Clinical MDR.<br> This is currently not supported from within the StudyBuilder app, so the user must initiate this by executing pipelines in the StudyBuilder System Azure Cloud environment.<br><br> Standards Developer also maintains dictionary terms within the StudyBuilder Library module. These are manually looked up on internet browsers and then entered into the system.<br><br> Main task for the Standards Developer is to maintain sponsor defined extensions to CDISC data standards as well as native concepts and syntax templates. |
| Study Setup User | Study Setup User manage study definitions, define study metadata, build study specifications and can list study metadata. |
| Read Only User<br>(and all other users) | Dedicated Read Only Users and all other system users can browse data for all library elements and study definitions from the StudyBuilder app. <br> They can also connect directly to the Clinical MDR graph database using SSO for browsing and exploring data via the defined NeoDash reports. <br> All users also have ccess to the user guides and system documentation via the documentation portal. |
| Downstream Systems | Can connect to the Clinical MDR API using dedicated user accounts or system accounts and access all data. |

> NOTES:
> - Confidential study definition access is planned but not yet implemented.
> - Integrations via Mulesoft API is planned but not yet implemented.
> - Initial data standards and migration load as well as migration load during transition period are not described here under system data flow. This will be described under section for data migration [to-be-made]'.



