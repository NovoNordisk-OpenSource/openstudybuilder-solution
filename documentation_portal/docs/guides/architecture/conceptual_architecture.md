# Conceptual Architecture

This section describes the conceptual architecture for OpenStudyBuilder and Clinical-MDR with upstream and downstream systems.

[![Conceptual architecture for the clinical-MDR and the StudyBuilder](/images/documentation/conceptual-architecture.png)](/images/documentation/conceptual-architecture.png)


 - **OpenStudyBuilder Documentation** Online documentation for the OpenStudyBuilder solution including introduction, user guides, system documentation and data model documentation.
 - **OpenStudyBuilder App** Vuetify based Web application with the UI for creating the study definition specification.
 - **Protocol Metadata add-in** Microsoft Word add-in tool holding the Protocol Template and import features of the structured study specification metadata that relates to the protocol content.
 - **Up-stream integrations** Integrations to upstream clinical systems like CTMS, Trial Supplies, EDC, Study Registries, etc.
 - **Down-stream integrations** Integrations to downstream clinical data systems for SDTM, ADaM, analysis and reporting.
 - **Explore data** FAIR based study search and explore tool utilizing the OpenStudyBuilder metadata with reference to systems holding study data.
 - **OpenStudyBuilder API** and **Standards Library API** Python based web application based on FastAPI framework supporting all CRUD actions to the database, access control, versioning, workflows and data integrity rules.
 - **Integration Service** Integration to UNIX based Statistical Computing Environment (SCE) with SAS and R.
 - **Clinical MDR** Neo4j linked graph database and data model supporting the library standards, study definitions including fine granularity of versioning, audit trail, workflows and access control.
 - **Standards Management** Integrated into the OpenStudyBuilder App as the Library module managing concepts, dictionaries, code lists, syntax templates, project and TA standards.

