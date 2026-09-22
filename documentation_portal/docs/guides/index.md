# Introduction to documentation

This site holds the online documentation for the OpenStudyBuilder solution.

The OpenStudyBuilder is a new approach to working with studies that, once fully implemented, will drive end-to-end consistency and more efficient processes - all the way from protocol development and CRF design- to creation of datasets, analysis, reporting and public disclosure of study information.

The OpenStudyBuilder consists of:

- the **OpenStudyBuilder application** (web-based user interface)
- the new **clinical Metadata Repository** database (central repository for all study specification data)
- the **API layer** (allowing interoperability with other systems)
- other **External tools** like Noe4j Dashboards and DB browser; a Word addin and some external scripts
- this **Complete Documentation portal**

![Open Study Builder Structure](/images/OSB_Structure.png)

The solution design is inspired by the CDISC 360 POC and the CDISC 360i following project. The intention is for the solution to be more and more compliant with the TransCelerate Digital Data Flow (DDF) reference implementation called the USDM. The complete OpenStudyBuilder solution is available as an Open Source project.

![Study Builder](/images/studybuilder-system.png)

**Benefits**

 - One set of controlled standards 
 - Easy maintenance of standards
 - Reuse of elements across studies
 - Enhanced search functionality
 - Direct exports of content into downstream systems

![Study Builder](/images/arrow-down.png)

 - Less need for QC
 - Less time spent resolving discrepancies
 - Faster document development

[![Conceptual Model](/images/WhatIsOSB.png)](/images/clinical-mdr-vision-v2.png)

# The OpenStudyBuilder includes

- A **Studies** part for specification of studies, including disease area and study type, objectives and endpoints, population, interventions, study design and schedule, activities and assessments

- A **Library** part for maintenance of terminology standards (incl. CDISC controlled terminology and external dictionaries for medical terms, pharmacological classes, units, etc.) as well as syntax templates for cross-study and cross-project standardisation

- An underlying **knowledge database** to enable complex queries and dashboards showing aggregated information
