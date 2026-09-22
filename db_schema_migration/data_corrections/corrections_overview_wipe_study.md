# Data corrections: overview of data_corrections.correction_wipe_study

PRD Data Corrections: Single Study Wipe



## 1. Correction: delete_unwanted_study

### Delete one complete study

#### Problem description
Sometimes studies are created by mistake in the production environment.
These occupy some Study IDs and cause confusion.
This script deletes all nodes and relationships related to a specific study.

#### Change description
Delete all nodes and relationships related to the study identified by the given study number and study UID.
If the study number and study UID do not match, no deletion will occur.

#### Nodes and relationships affected
- All study nodes for the study identified by the given study number and study UID.
