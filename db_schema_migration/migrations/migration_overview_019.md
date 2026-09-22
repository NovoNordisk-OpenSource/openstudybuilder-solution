# Release: 2.5 (x 2026)

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
- Removing all ODM nodes including deleted nodes

#### Nodes Affected
- `OdmAlias`
- `OdmDescription`
- `OdmFormalExpression`
- `OdmConditionRoot`
- `OdmConditionValue`
- `OdmMethodRoot`
- `OdmMethodValue`
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

### 2. Migrate codelist ordinal property
#### Change Description
- Rename the `ordinal` property on `CTCodelistAttributesValue` to `is_ordinal`

#### Nodes Affected
- `CTCodelistAttributesValue`

#### Relationships affected
- None
