# Release: 1.17.0 (post-August 2025)

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


### 3. Migrate `StudyDesingClass` to all existing Studies with value equal to `Manual`
#### Change Description
- Migrated `StudyDesignClass` StudySelection to each Active Study with the `Manual` value that indicates that Cohort stepper is not used to setup arms, branches and cohorts.

#### Nodes Affected
- `StudyDesignClass`
- `StudyValue`

#### Relationships affected
- `HAS_STUDY_DESIGN_CLASS`


### 4. Migrate `merge_branch_for_this_arm_for_sdtm_adam` boolean property for all `StudyArm` nodes
#### Change Description
- Added `merge_branch_for_this_arm_for_sdtm_adam` boolean property to `StudyArm` node with a default value equal to `False`
#### Nodes Affected
- `StudyArm`