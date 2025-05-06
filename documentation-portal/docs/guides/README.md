# Introduction to documentation

This site holds the online documentation for the StudyBuilder solution.

The StudyBuilder is a new approach to working with studies that, once fully implemented, will drive end-to-end consistency and more efficient processes - all the way from protocol development and CRF design- to creation of datasets, analysis, reporting and public disclosure of study information.

The StudyBuilder consists of:

- the **StudyBuilder app** (web-based user interface)
- the new **clinical Metadata Repository** (central repository for all study specification data)
- the **API layer** (allowing interoperability with other systems)

The solution design is inspired by the CDISC 360 POC and the intention is for the solution to become compliant with the TransCelerate Digital Data Flow (DDF) reference implementation. The complete StudyBuilder solution is planned to be made available as an Open Source project.

![Study Builder](~@source/images/studybuilder-system.png)

**Benefits**

 - One set of controlled standards 
 - Easy maintenance of standards
 - Reuse of elements across trials
 - Enhanced search functionality
 - Direct exports of content

![Study Builder](~@source/images/arrow-down.png)

 - Less need for QC
 - Less time spent resolving discrepancies
 - Faster document development

[![Conceptual Model](~@source/images/clinical-mdr-vision-v2.png)](../images/clinical-mdr-vision-v2.png)

# The StudyBuilder includes

- A **Studies** part for specification of studies, including disease area and study type, objectives and endpoints, population, interventions, study design and schedule, activities and assessments

- A **Library** part for maintenance of terminology standards (incl. CDISC controlled terminology and external dictionaries for medical terms, pharmacological classes, units, etc.) as well as syntax templates for cross-study and cross-project standardisation

- An underlying **knowledge database** to enable complex queries and dashboards showing aggregated information


