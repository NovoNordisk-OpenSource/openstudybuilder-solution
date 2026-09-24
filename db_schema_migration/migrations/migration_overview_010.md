# Release: 1.11.0 (post-December 2024)

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


### 3. Protocol SoA snapshot
----------------------------  
#### Change Description
- Save protocol SoA snapshot for all locked versions of all studies
  PR (commit `7f9cbabbf3d6`)

#### Relationships Affected
- HAS_PROTOCOL_SOA_CELL
- HAS_PROTOCOL_SOA_FOOTNOTE


### 4. User Identification
-------------------------------------  
#### Change Description
- Use `author_id` instead of `user_initials` field on all relevant nodes/relations to identify users performing actions.
- Retrieve IDs of all relevant users from Active Directory based on their initials.
- Create `User` nodes for all unique users that have performed any actions until now, and persist their `id, email/username`.


- Related PR (commit `336cf0adf597`).

#### Nodes and Relatiosnhips Affected
- `CTPackage, StudyAction, Edit, Create, Delete` nodes: `user_initials` field value copied to `author_id` field.
- `HAS_VERSION, HAS_TERM, HAD_TERM, LATEST_DRAFT, LATEST_LOCKED, LATEST_RELEASED` relations: `user_initials` field value copied to `author_id` field.
- `User`: new nodes created


### 5. Unifying StudyVisit window units for all StudyVisits in a Study
-------------------------------------  
#### Change Description
- All StudyVisits should have the same window unit across all StudyVisits in a single Study.
- If some Study used `week` unit for some of the StudyVisits it should be changed for `days`

- Related PR (commit `7986c0a642ff`).

#### Nodes Affected
- `:StudySelectionMetadata`



### 6. Updating UnitDefinition properties
-------------------------------------  
#### Change Description
- Updating values of `molecular_weight_conv_expon` from `0` to `false` and `1` to `true`
- Renamed `molecular_weight_conv_expon` to `use_molecular_weight`
- Added new `use_complex_unit_conversion` boolean property with value `false`

- Related PR (commit `598f958d0ddc`).

#### Nodes Affected
- `:UnitDefinitionValue`


### 7. Merge duplicated StudySoAGroup/StudyActivityGroup/StudyActivitySubGroup nodes that are having different visibility flags set
-------------------------------------
#### Change Description
- Merge duplicated nodes for `StudySoAGroup`, `StudyActivityGroup` and `StudyActivitySubGroup`.

- Related PR (commit `0001bb3f475e`).

#### Nodes Affected
- `StudySoAGroup`, `StudyActivityGroup` and `StudyActivitySubGroup`
