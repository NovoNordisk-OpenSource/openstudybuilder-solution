# Conceptual Architecture

This section describe the conceptual architecture for StudyBuilder and Clinical-MDR with upstream and downstream systems.

[![Conceptual architecture for the clinical-MDR and the StudyBuilder](~@source/images/documentation/conceptual-architecture.png)](../../images/documentation/conceptual-architecture.png)


 - **StudyBuilder Documentation** Online documentation for the StudyBuilder solution including introduction, user guides, system documentation and data model documentation.
 - **StudyBuilder App** Vutify based Web application with the UI for creating the study definition specification.
 - **Protocol Metadata add-in** Microsoft Word add-in tool holding the Protocol Template and import features of the structured study specification metadata that relates to the protocol content.
 - **Up-stream integrations** Integrations to up-stream clinical systems like CTMS, Trial Supplies, EDC, Study Registries, etc.
 - **Down-stream integrations** Integrations to down-stream clinical data systems for SDTM, ADaM, analysis and reporting.
 - **Explore data** FAIR based study search and explore tool utilising the StudyBuilder metadata with reference to systems holding study data.
 - **StudyBuilder API** and **Standards Library API** Python based web application based on FAST API framework supporting all CRUD actions to the database, access control, versioning, workflows and data integrity rules.
 - **Integration Service** Integration to UNIX based Statistical Computing Environment (SCE) with SAS and R.
 - **Clinical MDR** Neo4j linked graph database and data model supporting the library standards, study definitions including fine granularity of versioning, audit trail, workflows and access control.
 - **Standards Management** Integrated into the StudyBuilder App as the Library module managing concepts, dictionaries, code lists, syntax templates, project and TA standards.



