# Architectural Decision Records

This section describe the [Architectural Decision Record](https://adr.github.io/) (ADR) for the StudyBuilder system.

The ADR is described as:

- **Title** A short noun phrase containing the architecture decision
- **Context** In this section of the ADR we will add a short one- or twosentence description of the problem, and list the alternative solutions.
- **Decision** In this section we will state the architecture decision and provide a detailed justification of the decision.
- **Consequences** In this section of the ADR we will describe any consequences after the decision is applied, and also discuss the trade-offs that were considered.

## We will use a label property graph database as the storage component

### Context

The StudyBuilder solution will be an MDR solution holding highly interrelated clinical data standards - both imported from external sources as well as sponsor defined extension. These will be enriched with biomedical concepts definitions binding these with end-to-end linage across data standards for various needs.

The data standards in the MDR component (the library part) will then be applied in study specifications in the SDR part, with relationship to the standard elements in the MDR (library part).

All of this needs to be managed with a fine granularity of versioning and audit trail.

Many previous attempts in managing this in large relational data models, or very generic relational data models, have failed due to complexity in data representation, query performance and maintainability.

### Decision

The data structures in the StudyBuilder solution, as a combined MDR and SDR, will apply highly connected data with many relationships. The data domain is very large and complex.

Therefore, we have decided to use a label property graph database, applying a semantic domain driven data model design close to the clinical data standards domain. The Neo4j labeled property graph database system have been chosen as the most widely used and supported graph database.

This will in a better way represent the many relationships in data than traditional relational databases, and be simpler to use for clinical data standrds domain experts - while still complex for others, as the clinical data standards domain is complex. 

The representation of versioning and audit trail will be captured by relationship properties, giving a generic approach for managing versioning and audit trail information in a combined structure indepedent from the node attributes. See more details in [MDR Data Architecture](mdr_data_architecture).

This will enable faster queries by any version or the latest version.

The system database will actually represent a knowledge graph of clinical data standards and their usage in study specifications. To leverage this the system users should be default also get read only access to the system graph database so the use of native graph database exploration and visualization tools can be enabled (like [NeoDash](https://neo4j.com/labs/neodash/)).

### Consequences

The StudyBuilder solution is fully API based, so the API service layer must be managing all transactions, including managing the versioning and audit trail capabilities in the label property grap database.

As the end users also have direct database access, the graph database must support named Single Sign On (SSO) and data level access control.

Any non-graph enabled tools must connect to the system using the API, as relational SQL database based data integrations not will be possible.

RDF based tools can be connected to the system via the [neosemantic](https://neo4j.com/labs/neosemantics/) toolkit. This is however currently not setup for the StudyBuilder system.





