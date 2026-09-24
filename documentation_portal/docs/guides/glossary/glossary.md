# Glossary

| Term (abbreviation) | Definition |
| :------------------ | :------------------------------------ |
| 	Activity	 | 	An action, undertaking, or event, which is anticipated to be performed or observed, or was performed or observed, according to the study protocol during the execution of the study (USDM CT).	 |
| 	Activity Instance	 | 	The detailed specification of an Activity's observation, including context/qualifier values and references to standards such as SDTM and ADaM, used to uniquely identify how the activity is collected and represented (USDM CT).	 |
| 	Antibody (AB)	 | 	The assessment group covering antibody / immunogenicity data collected in a study, kept separate from laboratory (LAB) and pharmacokinetic/pharmacodynamic (PK/PD) assessments to avoid duplication.	 |
| 	Audit Trail	 | 	A chronological, GCP-compliant record of who changed what, when, and why, across a system's library elements and/or study definitions.	 |
| 	Biomedical Concept (BC)	 | 	A unit of biomedical knowledge created from a unique combination of characteristics that include implementation details like variables and terminologies, used as building blocks for standardized, hierarchically structured clinical research information (USDM CT).	 |
| 	Case Report Form (CRF)	 | 	A paper or electronic form used to collect data from a study subject, structured into item groups and items (CDISC ODM).	 |
| 	CDISC	 | 	[Clinical Data Interchange Standards Consortium](https://www.cdisc.org/about).	 |
| 	Controlled Terminology (CT)	 | 	Controlled Terminology refer to code lists and terminology values. In this context, it covers [CDISC CT](https://www.cdisc.org/standards/terminology/controlled-terminology) managed in collaboration with [National Cancer Institute's Enterprise Vocabulary Services (EVS)](https://evs.nci.nih.gov), as well as sponsor-defined CT managed by a pharmaceutical company.	 |
| 	Digital Data Flow (DDF)	 | 	The DDF initiative will help to modernize clinical trials by enabling a digital workflow to allow for the automated creation of study assets and configuration of study systems to support clinical trial execution. This initiative will establish a foundation for a future state of automated and dynamic readiness that can transform the drug development process. <br> TransCelerate has collaborated with CDISC and other stakeholders to develop a standard data model for specifying protocol information, as well as a demonstrated way to connect systems that produce, exchange or consume this information.	 |
| 	Implementation Guide (IG)	 | 	A CDISC standard providing detailed conventions for implementing a data model (for example SDTM) for a specific use, such as the SDTM Implementation Guide (SDTMIG).	 |
| 	Laboratory Data (LAB)	 | 	The assessment group covering local or central laboratory data collected in a study, kept separate from pharmacokinetic/pharmacodynamic (PK/PD) and antibody (AB) assessments to avoid duplication.	 |
| 	Metadata Repository (MDR)	 | 	Metadata Repository is an IT system managing definitions about clinical data standards definitions, data concepts and controlled terminologies.	 |
| 	Parent Template	 | 	A base Syntax Template from which pre-instance templates and template instantiations are derived.	 |
| 	Pharmacodynamic (PD)	 | 	The study of a drug's biochemical and physiological effects on the body; commonly grouped with pharmacokinetic (PK) assessments in study data.	 |
| 	Pharmacokinetic (PK)	 | 	The study of how a drug moves through the body, absorption, distribution, metabolism and excretion; commonly grouped with pharmacodynamic (PD) assessments in study data.	 |
| 	Pre-Instance Template	 | 	A pre-instantiation of a Parent Template, created to support study search and selection; not yet related to a specific study.	 |
| 	Reason for Change	 | 	A GCP-compliant justification captured for a change to library or study metadata; for library elements this is captured per change, for studies it is captured at study lock.	 |
| 	Schedule of Events (SoA)	 | 	A standardized representation of planned clinical trial activities including interventions (e.g., administering drug, surgery) and study administrative activities (e.g., obtaining informed consent, distributing clinical trial material and diaries, randomization) as well as assessments. See also schedule of assessments. Compare to study design schematic (CDISC Glossary).	 |
| 	Sponsor Model	 | 	A data model that layers sponsor-specific extensions on top of a CDISC standard model (for example SDTM), rather than replacing it.	 |
| 	Study Element	 | 	A basic building block for time within a clinical study comprising the following characteristics: a description of what happens to the subject during the element; a definition of the start of the element; a rule for ending the element (USDM CT).	 |
| 	Study Epoch	 | 	A named time period defined in the protocol, wherein a study activity is specified and unchanging throughout the interval, to support a study-specific purpose (USDM CT).	 |
| 	Syntax Template	 | 	A standardized pattern used for the arrangement of words and phrases to create well-formed, structured sentences (USDM CT).	 |
| 	Template Instantiation	 | 	A Syntax Template actually used on a study, derived from a Parent Template directly or via a Pre-Instance Template.	 |
| 	Unified Study Definition Model (USDM)	 | 	The USDM comprises 4 parts, which are official CDISC standards: <br> 1. Unified Study Definitions Model (USDM) class diagram represented as a unified modeling language (UML) class diagram <br> 2. Application programming interface (API) specification <br> 3. CDISC Controlled Terminology <br> 4. Unified Study Definitions Model Implementation Guide (USDM-IG) <br> [CDISC-DDF](https://www.cdisc.org/ddf)	 |


## References

- [Overview of Digital Dataflow resources](https://www.cdisc.org/ddf)
- [CDISC Glossary](https://www.cdisc.org/standards/glossary)
- [DDF/USDM CT](https://github.com/cdisc-org/DDF-RA/blob/v3.0.0/Deliverables/CT/USDM_CT.xlsx) and direct [NCI reference](https://evs.nci.nih.gov/ftp1/CDISC/DDF/)