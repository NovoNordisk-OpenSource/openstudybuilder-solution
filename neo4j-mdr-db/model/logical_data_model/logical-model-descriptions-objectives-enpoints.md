# Desription of Logical Data Model for Library of Objectives and Endpoints

This document describe the entities in diagram: logical-model-objectives-endpoints.graphml.

The Objectives and Endpoints are part of the top levels of the conceptual standards that refer to Activities and Assessments. These can exist both as part of the CDISC 360 concept based standards as well as sponsor defined concept standards.

| Entity | Definition | Example |
| ------ | ---------- | -------- |
| Library                | Entity holds the name and definition of the library that are the source and owner for the elements in the library. | The CDISC Library and a specific sponsors library.  |
| ObjectiveTemplate      | A sentence syntax for an objective text including reference to parameters that can be replaced with standardized values. | To demonstrate superiority in the efficacy of [StudyIntervention] to [ComparatorIntervention] in [Assessment] |
| Objective              | A sentence that represent a specific objective sentence based on a template where the parameters are replaced with specific standardized values. | To demonstrate superiority in the efficacy of human insulin to Metformin in HbA1c |
| EndpointTemplate       | A sentence syntax for an endpoint text including reference to parameters that can be replaced with standardized values. | Mean Change from Baseline in [Assessment] after [Timeframe] ([Unit]) |
| TemplateParameter      | A sentence that represent a specific endpoint sentence based on a template where the parameters are replaced with specific standardized values. | Mean Change from Baseline in HbA1c after 26 weeks (%) |
| TemplateParameterValue | Hold the specific standardized values for template parameters. These are categorised by the specific types of template parameters. | human insulin (StudyIntervention), HbA1c (Assessment) |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |




