---
title: Data Model Overview
date: 2021-06-06
---

# Physical Data Model Overview
The physical data model represent the actual data as it is stored in the database. 
For the Sponsor Study MDR system, the database of choice is a [Labeled Property Graph](https://en.wikipedia.org/wiki/Graph_database#Labeled-property_graph) database (Neo4j).
This document therefore describe the structure of the stored nodes and relationships (with properties) as stored in Neo4j.

## High-Level Overview
To best get an understanding of the overall structure of the physical data model, we divide it into six parts:
1. **Studies** (Study Properties, Fields, and Selections)
2. **Library Objects** (Objectives, Endpoints, and Timeframes)
3. **Configuration Values** (Field and Selection Configurations)
4. **Control Terminology** (Catalogues, Packages, Codelists, and Terms)
5. **Dictionaries** (Concepts, UCUM, UNII, PClass, and more)
6. **Assessments** (Reminders, Findings, Compounds, and more)

The image below shows how these six parts are interconnected.
<a :href="$withBase('/model/physical_data_model/high-level-neo4j-model.png')" target="_blank" class="tertiary--text footer-links">
    ![Physical Data Model (High Level)](~@source/images/model/physical_data_model/high-level-neo4j-model.png)
</a>

*A high-level view of the components of the physical data model, as of August 4, 2021*

## Components
The relationships between these parts are as follows:
- **Studies** use **Configurations** to set study fields and study selections.
- **Studies** use data from **Library Objects** as selections.
- **Studies** use data from **Control Terminology** as fields.
- **Studies** use data from **Assessments**.
- **Library Objects** have a set of defined Template Parameters, from **Control Terminology** or **Dictionaries**.
- **Assessments** have types as defined in **Control Terminology**.


For each of the six parts, a page is available in the documentation. Each page will address four points:
1. A summary of what the part of the model is used for.
2. A list of the node labels and relationship types defined in the part of the model. (A data dictionary)
3. The business logic performed on the part of the model.
4. Details on how the part of the model is connected to other parts of the global physical data model.

To view the physical data model in its entirity, open the [master model file](https://orgremoved.visualstudio.com/Clinical-MDR/_git/neo4j-mdr-db?path=%2Fmodel%2Fphysical_data_model%2Fneo4j-model.graphml) using a graphml editor.
(Recommended: the [yWorks YED Graph Editor](https://www.yworks.com/products/yed))

