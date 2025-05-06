---
title: Domain Data Model
date: 2020-11-14
---

# Domain Data Model

The domain data model represent the data model as how the data is returned from the API calls. The domain data model is made as an Object-Oriented class diagram representing the returned result file from an API call. This can be represented in various exchange file formats like JSON, XML, CSV, etc., but for the Clinical MDR system this will mainly be in JSON. For some API endpoints other file formats will be supported, these can be used to support exports into other systems.

As an example see below diagram for Objectives Templates data domain – sub part of the conceptual standards subject area, coresponding to the /objective-templates API endpoint. This is identical for both the Industry Standards and the Sponsor Standards – depending on the relationship to the Library entity.

[![Diagram: Domain Model Objective Templates](~@source/images/model/domain_data_model/domain-model-objectives.png)](../../images/model/domain_data_model/domain-model-objectives.png)

A detailed description of the domain data model by each API endpoint, or data domain, is available here:

[![Diagram: Domain Model Objective Templates](~@source/images/model/domain_data_model/domain-model.png)](../../images/model/domain_data_model/domain-model.png)

