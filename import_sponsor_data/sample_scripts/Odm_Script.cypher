MATCH (n1:Library {name: 'Sponsor'})
CREATE (n2:OdmFormRoot {uid: apoc.create.uuid()})-[r1:HAS_VERSION {change_description:'Initial', versionend_date:datetime(), start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(n3:OdmFormValue {oid:'F.VS', repeating: False, name: 'VITAL SIGNS'})
CREATE (n2)-[r2:LATEST]->(n3)
CREATE (n1)-[r3:CONTAINS_CONCEPT]->(n2)
CREATE (n3)-[h:HAS_DESCRIPTION]->(n4:OdmDescription {uid: apoc.create.uuid(), language: 'ENG', description: 'Vital signs form', instruction: 'Please complete this Vital Sign form before starting the treatment'})
RETURN n1, n2, n3, n4

MATCH (n1:Library {name: 'Sponsor'})
CREATE (n2:OdmItemGroupRoot {uid: apoc.create.uuid()})-[r1:HAS_VERSION {change_description:'Initial', versionend_date:datetime(), start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(n3:OdmItemGroupValue {oid:'G.VS.VSBP', repeating: False, name: 'Vital Signs for Blood Pressure',  is_reference_data: 'No', sas_dataset_name: 'BLOODPRE',})
CREATE (n2)-[r2:LATEST]->(n3)
CREATE (n1)-[r3:CONTAINS_CONCEPT]->(n2)
CREATE (n3)-[h:HAS_DESCRIPTION]->(n4:OdmDescription {uid: apoc.create.uuid(), language: 'ENG', description: 'Vital signs Item Group for Blood Pressure', instruction: 'Please complete this Vital Sign item group for each blood pressure measurement'})
RETURN n1, n2, n3, n4

MATCH (n1:Library {name: 'Sponsor'})
MERGE (n2:OdmItemRoot {uid: apoc.create.uuid()})-[r1:HAS_VERSION {change_description:'Initial', versionend_date:datetime(), start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(n3:OdmItemValue {oid:'I.SYSBP', name: 'Systolic blood pressure', data_type: 'integer', lengh: 3, sas_field_name: 'SYSBP', sds_var_name: 'VSORRES', origin: 'CRF'})
MERGE (n2)-[r2:LATEST]->(n3)
MERGE (n1)-[r3:CONTAINS_CONCEPT]->(n2)
MERGE (n3)-[h:HAS_DESCRIPTION]->(n4:OdmDescription {uid: apoc.create.uuid(), language: 'ENG', description: 'Systolic blood pressure of the patient', instruction: 'Please provide this Systolic blood pressure with the laterality, the position and the localisation'})
RETURN n1, n2, n3, n4

MATCH (n1:Library {name: 'Sponsor'})
MERGE (n2:OdmItemRoot {uid: apoc.create.uuid()})-[r1:HAS_VERSION {change_description:'Initial', versionend_date:datetime(), start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(n3:OdmItemValue {oid:'I.DIABP', name: 'Diastolic blood pressure', data_type: 'integer', lengh: 3, sas_field_name: 'DIABP', sds_var_name: 'VSORRES', origin: 'CRF'})
MERGE (n2)-[r2:LATEST]->(n3)
MERGE (n1)-[r3:CONTAINS_CONCEPT]->(n2)
MERGE (n3)-[h:HAS_DESCRIPTION]->(n4:OdmDescription {uid: apoc.create.uuid(), language: 'ENG', description: 'Diastolic blood pressure of the patient', instruction: 'Please provide this Diastolic blood pressure with the laterality, the position and the localisation'})
RETURN n1, n2, n3, n4

MATCH (n1:Library {name: 'Sponsor'}), (n5:CTCodelistRoot {uid: 'C74456'})
MERGE (n2:OdmItemRoot {uid: apoc.create.uuid()})-[r1:HAS_VERSION {change_description:'Initial', versionend_date:datetime(), start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(n3:OdmItemValue {oid:'I.LOCBP', name: 'Blood pressure localisation', data_type: 'string', lengh: 3, sas_field_name: 'VSLOC', sds_var_name: 'VSLOC', origin: 'Protocol'})
MERGE (n2)-[r2:LATEST]->(n3)
MERGE (n1)-[r3:CONTAINS_CONCEPT]->(n2)
MERGE (n3)-[h:HAS_DESCRIPTION]->(n4:OdmDescription {uid: apoc.create.uuid(), language: 'ENG', description: 'Blood pressure localisation', instruction: 'Please provide the localisation where the blood pressure was taken'})
MERGE (n3)-[r4:HAS_CODELISTREF]->(n5:CTCodelistRoot)
RETURN n1, n2, n3, n4, n5