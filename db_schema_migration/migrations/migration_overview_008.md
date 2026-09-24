# Release: post-September 2024

## Common migrations

### 1. Indexes and Constraints
-------------------------------------
#### Change Description
- Re-create all db indexes and constraints according to [db schema definition](../../db/db_schema.py).


### 2. CT Config Values (Study Fields Configuration)
-------------------------------------  
#### Change Description
- Re-create all `CTConfigValue` nodes according to values defined in [this file](../../import_sponsor_data/datafiles/configuration/study_fields_configuration.csv).

#### Nodes Affected
- CTConfigValue


## Release specific migrations

### 1. Library Compounds
-------------------------------------  
#### Change Description
- Re-create all Compound and CompoundAlias entities. Introduce ActiveSubstance, PharmaceuticalProduct and MedicinalProduct entities.

#### Nodes Affected
- Existing `CompoundRoot/Value`, `CompoundAliasRoot/Value` nodes removed, together with any relationships from/to them.
- New `CompoundRoot/Value`, `CompoundAliasRoot/Value`, `ActiveSubstanceRoot/Value`, `PharmaceuticalProductRoot/Value`, `MedicinalProductRoot/Value` nodes created.


### 2. Study Compounds
-------------------------------------  
#### Change Description
- Remove all existing StudyCompound and StudyCompoundDosing selections from all studies.

#### Nodes Affected
- Existing `StudyCompound`, `StudyCompoundDosing` nodes removed, together with any relationships from/to them.


## 3. Numbers for Non-Visit and Unscheduled-Visit should be changed.
-------------------------------------  
### Change Description
- The visit properties that contain Non-visit and Unscheduled-Visit numbers should be changed.
- The currently implementation says that Unscheduled-Visit number is `29500` and Non-Viist number is `29999`.
- These numbers should be reversed.

- Related PR (commit `3f839aaf8ca0`).

### Nodes Affected
  - `StudyVisit`