# Release: 2.7 (x 2026)

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

### 1. Migrate ODM nodes and relationships
-------------------------------------
#### Change Description
- Replaced all ODM nodes' `ConceptRoot`/`ConceptValue` label with `OdmRoot`/`OdmValue`
- Added `Odm` label to all ODM nodes
- Replaced `CONTAINS_CONCEPT` relationship from `Library` to ODM nodes with `CONTAINS_ODM`

#### Nodes Affected
- `OdmAlias`
- `OdmTranslatedText`
- `OdmFormalExpression`
- `OdmConditionValue`
- `OdmConditionRoot`
- `DeletedOdmConditionRoot`
- `OdmMethodValue`
- `OdmMethodRoot`
- `DeletedOdmMethodRoot`
- `OdmFormValue`
- `OdmFormRoot`
- `DeletedOdmFormRoot`
- `OdmItemGroupValue`
- `OdmItemGroupRoot`
- `DeletedOdmItemGroupRoot`
- `OdmItemValue`
- `OdmItemRoot`
- `DeletedOdmItemRoot`
- `OdmStudyEventValue`
- `OdmStudyEventRoot`
- `DeletedOdmStudyEventRoot`
- `OdmVendorNamespaceValue`
- `OdmVendorNamespaceRoot`
- `DeletedOdmVendorNamespaceRoot`
- `OdmVendorAttributeValue`
- `OdmVendorAttributeRoot`
- `DeletedOdmVendorAttributeRoot`
- `OdmVendorElementValue`
- `OdmVendorElementRoot`
- `DeletedOdmVendorElementRoot`
