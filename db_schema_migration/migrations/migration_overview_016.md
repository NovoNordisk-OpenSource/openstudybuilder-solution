# Release: 2.0.0

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

### 1. Removal of ODM data
-------------------------------------  
#### Change Description
- The ODM data (CRF forms etc) is very complicated to migrate correctly to the new ct model.
  Since this data is not currently used, and can easily be recreated,
  this migration removes the data to avoid the migration.

#### Nodes Affected
- `OdmDescriptionRoot`
- `OdmDescriptionValue`
- `OdmAliasRoot`
- `OdmAliasValue`
- `OdmConditionRoot`
- `OdmConditionValue`
- `OdmMethodRoot`
- `OdmMethodValue`
- `OdmFormalExpressionRoot`
- `OdmFormalExpressionValue`
- `OdmFormRoot`
- `OdmFormValue`
- `OdmItemGroupRoot`
- `OdmItemGroupValue`
- `OdmItemRoot`
- `OdmItemValue`
- `OdmStudyEventRoot`
- `OdmStudyEventValue`
- `OdmVendorNamespaceRoot`
- `OdmVendorNamespaceValue`
- `OdmVendorAttributeRoot`
- `OdmVendorAttributeValue`
- `OdmVendorElementRoot`
- `OdmVendorElementValue`


### 2. Cleanup of activity items
-------------------------------------  
#### Change Description
- A few activity items have been incorrectly linked to the wrong ct terms,
  for example the milligram unit instead of a magnesium measurement.
  This migration relinks these instances to the correct terms,
  which allows the following CT model migration to succeed.

#### Nodes Affected
- `ActivityItem`


### 3. Migration of test_name_code activity items
-------------------------------------  
#### Change Description
- The `test_name_code` activity item class that combines a test name and test code
  in a single node is not supported in the new ct model.
  This migration replaces these activity items with separate items for `test_name` and `test_code`,
  and removes the `test_name_code` item class.

#### Nodes Affected
- `ActivityItemClassRoot`
- `ActivityItemClassValue`
- `ActivityItem`


### 4. CT model refactoring
-------------------------------------  
#### Change Description
- Refactored CT to new model.
- `CTCodelistTerm` is added between `CTCodelistRoot` and `CTTermRoot`. `HAS_TERM` now joins `CTCodelistRoot` and `CTCodelistTerm`, and a new `HAS_TERM_ROOT` relationship is created between `CTCodelistTerm` and `CTTermRoot`. `HAD_TERM` relationships are abandoned.
- `CTTermContext` is added between non-CT nodes and pairs of `CTTermRoot` and `CTCodelistRoot`. For example, instead of a relationship between `UnitDefinitionValue` and a `CTTermRoot` belonging to several codelists, this relationship now joins `UnitDefinitionValue` and a `CTTermContext`, this node joining the `CTTermRoot` and a single `CTCodelistRoot`.

Note: This migration checks if any new CT was sideloaded before running. Run the mdr-standards-import script with sideload option turned on before applying the migration.

#### Nodes Affected
- All CT related nodes will be dropped and replaced with the new CT

#### Edges Affected
- `HAS_TERM`
- `HAD_TERM` (removed)
- All relationships between non-CT nodes and CTTermRoot:
  - `REFERENCES_TERM`
  - `HAS_CT_DIMENSION`
  - `HAS_DATA_DOMAIN`
  - `HAS_SDTM_DOMAIN`
  - `HAS_CT_UNIT`
  - `HAS_CODELIST_TERM`
  - `HAS_REASON_FOR_NULL_VALUE`
  - `HAS_EPOCH_SUB_TYPE`
  - `HAS_EPOCH_TYPE`
  - `HAS_EPOCH`
  - `HAS_DOSAGE_FORM`
  - `HAS_ROUTE_OF_ADMINISTRATION`
  - `HAS_CONFIGURED_TERM`
  - `HAS_OBJECTIVE_LEVEL`
  - `HAS_ENDPOINT_LEVEL`
  - `HAS_TYPE`
  - `HAS_CATEGORY`
  - `HAS_DOSE_FREQUENCY`
  - `HAS_UNIT_SUBSET`