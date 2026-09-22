## Data corrections: overview of data_corrections.correction_015

PRD Data Corrections: Before Release 2.1



## 1. Correction: change_visit_window_unit_from_weeks_to_days_study_000137

#### Problem description
Study_000137 has selected 'weeks' for the window unit for all visits in their Study.
They would like to change it to 'days' instead but API doesn't allow to change window units after study visits are created.
This data-correction changes the window unit from 'weeks' to 'days' for all StudyVisits in Study_000137.

#### Change description
- Update (:StudyVisit)-[:HAS_WINDOW_UNIT]->(:UnitDefinitionRoot) relationship to point to 'days' unit definition.

#### Nodes and relationships affected
- `StudyVisit` node
- `HAS_WINDOW_UNIT` relationship

#### Expected changes: 13 relationships removed and 13 relationships created.
