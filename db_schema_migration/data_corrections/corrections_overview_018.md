## Data corrections: overview of data_corrections.correction_018

PRD Data Corrections: Before Release 2.7



## 1. Correction: fix_duplicated_study_visits_from_study_cloning

#### Problem description
Due to a bug in the Study cloning functionality, some StudyVisit nodes are linked to
multiple StudyEpoch nodes via the STUDY_EPOCH_HAS_STUDY_VISIT relationship. This causes
the study-visits API endpoint to return duplicate entries for the affected StudyVisit.
#### Change description
- Detect StudyVisit duplications by checking if any study visit uid appears more than once
  in the response of the /studies/{study_uid}/study-visits API endpoint.
- For each duplicated StudyVisit, remove the STUDY_EPOCH_HAS_STUDY_VISIT relationship to
  the StudyEpoch that belongs to a StudyValue which also has HAS_PROTOCOL_SOA_CELL relationships.
#### Nodes and relationships affected
- `STUDY_EPOCH_HAS_STUDY_VISIT` relationships
#### Expected changes: 3 `STUDY_EPOCH_HAS_STUDY_VISIT` relationships removed
