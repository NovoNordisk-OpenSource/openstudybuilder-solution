# Introduction to 4+1 architectural views

This section describes the StudyBuilder solution architecture from both a functional and technical point of view.  This section thereby fulfils the need for the overall functional and technical system documentation.

The architectural description is structured by the [4+1 architectural view model](https://en.wikipedia.org/wiki/4%2B1_architectural_view_model).

[![4+1 View Model](~@source/images/documentation/architecture-4+1-model.svg)](../../images/documentation/architecture-4+1-model.svg)

> Note, not all system diagrams and artefacts will be shared, and some are work in progress and will be shared on an ongoing basis.

Within each of the 4+1 views the following diagrams or artifacts are currently used, in progress, or coming soon – here displayed in the 4+1 model order.

## Logical View

  - [**System user guides**](../userguide/userguides_introduction.md)
    - The user guides are part of the system documentation including screen layout and user instructions.
  - **Conceptual, logical and physical data models**
    - As StudyBuilder is a very data centric repository solution the data models is important for the end-users understanding of the system usage
    - The conceptual model defines the information scope of the system; the logical the semantic definitions of the various data structures in the system; and the physical the actual implementation in the database.
    - As the end-user also have direct access to the underlying linked graph database, the physical model is part of the 'logical view'.
    - The data models are not yet shared in this online documentation portal, but will be added in a release soon.

## Process View

  - [**Integration Architecture**](integration_architecture)
    - Describe the current in- and outbound system integrations.
    - Note, additional outbound integrations will be defined soon.
  - [**System Data Flows**](system_data_flows)
    - Describe the current system user roles interactions and main data flows between system components
  - [**System Workflows**](system_workflows)
    - Describe the user interaction workflows in the system illustrated in activity diagrams and short activity descriptions.

## Development View

  - [**Conceptual Architecture**](conceptual_architecture)
    - Visual overview of the StudyBuilder solution with generic upstream and downstream systems and main internal system components including short description of each component.
  - [**System Component Architecture**](system_component_architecture)
    - Detailed overview of system components and interaction/data flows with descrition of each component, license, technology, git code repository.
  - [**Architectural Decision Records**](architectural_decision_records)
    - An Architectural Decision Record (ADR) consists of a short text describing a specific architecture decision.
    - At the moment only few of our acthitectural desisions have been documented, more will be adding in the coming period to improve our system documentation.

## Physical View
  - [**Cloud Architecture**](cloud_architecture)
    - Detailed Azure infrastructure schema diagrams and resource overviews.
  - [**Application Architecture**](application_architecture)
    - General describtion of the internal application architecture for the StudyBuilder API service layer component.
  - [**API Architecture**](mdr_api_architecture)
    - General description of the API service layer form an API usage point of view.
    - Include reference to the OpenAPI (Swagger) online documentation for the API service.
    - This section do need some cleanup and additions to be aligned with the latest solution design.
  - [**Database Architecture**](mdr_data_architecture)
    - General description of the data modeling principles applied in graph database.
    - The documentation of the physical data model will be added in this documentation portal at a later release.
  - [**Authentication and Authorisation Architecture**](authentication_authorisation_architecture)
    - General description of the Authentication and Authorisation setup including component interaction diagram.

## Use Case View
  - **High level use cases**
    - Use case descriptions based on value statements.
    - The use cases is work in progress and not shared yet.
  - **User requirements**
    - The user reqirements are written in user story format.
    - The user requirements is work in progress and not shared yet.


We will within this online documentation present the various diagrams and descriptions in a logical structure and sequence to facilitate readability as listed in the table of content in the left side panel.


> Tips:
> - In the upper right corner the online documentation portal support free text search.
> - At the bottom of each page, you can navigate to next or previous page as in an e-book.


