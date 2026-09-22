// Metadata: For the Template metadata
// library,oid,name,effectivedate,retireddate
LOAD CSV WITH HEADERS FROM 'file:///odm_templates.csv' AS row
MATCH (Library:Library {name: row.library})
MERGE (TemplateRoot:ConceptRoot:OdmTemplateRoot {uid: row.oid})
MERGE (TemplateValue:ConceptValue:OdmTemplateValue {oid: row.oid, name: row.name, effective_date: row.effectivedate, retired_date: row.retireddate})
MERGE (Library)-[r0:CONTAINS_CONCEPT]->(TemplateRoot)
MERGE (TemplateRoot)-[r1:LATEST_DRAFT {change_description:'Initial', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(TemplateValue)
MERGE (TemplateRoot)-[r2:LATEST]->(TemplateValue);

// Metadata: For the Form metadata
// library,oid,name,repeating,language,description,instruction
LOAD CSV WITH HEADERS FROM 'file:///odm_forms.csv' AS row
MATCH (Library:Library {name: row.library})
MERGE (FormRoot:ConceptRoot:OdmFormRoot {uid: row.oid})
MERGE (FormValue:ConceptValue:OdmFormValue {oid: row.oid, name: row.name, repeating: toBoolean(row.repeating)})
MERGE (DescriptionRoot:ConceptRoot:OdmDescriptionRoot {uid: row.oid+'.DESC'})
MERGE (DescriptionValue:ConceptValue:OdmDescriptionValue {language: row.language, name: row.name, description: row.description, instruction: COALESCE(row.instruction,'')})
MERGE (Library)-[r0:CONTAINS_CONCEPT]->(FormRoot)
MERGE (FormRoot)-[r1:LATEST_DRAFT {change_description:'Initial', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(FormValue)
MERGE (FormRoot)-[r2:LATEST]->(FormValue)
MERGE (FormRoot)-[r3:HAS_DESCRIPTION]->(DescriptionRoot)
MERGE (DescriptionRoot)-[r4:LATEST_DRAFT {change_description:'Initial', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(DescriptionValue)
MERGE (Library)-[r5:CONTAINS_CONCEPT]->(DescriptionRoot)
MERGE (DescriptionRoot)-[r6:LATEST]->(DescriptionValue);

// Metadata: For the ItemGroup metadata
// library;oid;name;repeating;isreferencedata;sasdatasetname;domain;origin;purpose;comment;language;description;instruction
LOAD CSV WITH HEADERS FROM 'file:///odm_itemgroups.csv' AS row
MATCH (Library:Library {name: row.library})
MATCH (cttermroot:CTTermRoot {uid: row.domain})
MERGE (ItemGroupRoot:ConceptRoot:OdmItemGroupRoot {uid: row.oid})
MERGE (ItemGroupValue:ConceptValue:OdmItemGroupValue {oid: row.oid, name: row.name, repeating: toBoolean(row.repeating), is_reference_data: COALESCE(toBoolean(row.isreferencedata),''), sas_dataset_name: COALESCE(row.sasdatasetname,''), origin: COALESCE(row.origin,''), purpose: COALESCE(row.purpose,''), comment: COALESCE(row.comment,'')})
MERGE (ItemGroupRoot)-[r7:HAS_SDTM_DOMAIN]->(cttermroot)
MERGE (DescriptionRoot:ConceptRoot:OdmDescriptionRoot {uid: row.oid+'.DESC'})
MERGE (DescriptionValue:ConceptValue:OdmDescriptionValue {language: row.language, name: row.name, description: row.description, instruction: COALESCE(row.instruction,'')})
MERGE (Library)-[r0:CONTAINS_CONCEPT]->(ItemGroupRoot)
MERGE (ItemGroupRoot)-[r1:LATEST_DRAFT {change_description:'Initial', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(ItemGroupValue)
MERGE (ItemGroupRoot)-[r2:LATEST]->(ItemGroupValue)
MERGE (ItemGroupRoot)-[r3:HAS_DESCRIPTION]->(DescriptionRoot)
MERGE (DescriptionRoot)-[r4:LATEST_DRAFT {change_description:'Initial', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(DescriptionValue)
MERGE (Library)-[r5:CONTAINS_CONCEPT]->(DescriptionRoot)
MERGE (DescriptionRoot)-[r6:LATEST]->(DescriptionValue);

// Metadata: For the Item metadata
// library,oid,name,prompt,datatype,length,significantdigits,codelist,term,unit,sasfieldname,sdsvarname,origin,comment,language,description,instruction
LOAD CSV WITH HEADERS FROM 'file:///odm_items.csv' AS row
MATCH (Library:Library {name: row.library})
MERGE (ItemRoot:ConceptRoot:OdmItemRoot {uid: row.oid})
MERGE (Library)-[r0:CONTAINS_CONCEPT]->(ItemRoot)
MERGE (ItemValue:ConceptValue:OdmItemValue {oid: row.oid, name: row.name, prompt: COALESCE(row.prompt,''), datatype: row.datatype, length: row.length, significant_digits: row.significantdigits, codelist: COALESCE(row.codelist,''), term: COALESCE(row.term,''), unit: COALESCE(row.unit,''), sas_field_name: row.sasfieldname, sds_var_name: row.sdsvarname, origin:row.origin, comment: COALESCE(row.comment,'')})
MERGE (DescriptionRoot:ConceptRoot:OdmDescriptionRoot {uid: row.oid+'.DESC'})
MERGE (DescriptionValue:ConceptValue:OdmDescriptionValue {language: row.language, name: row.name, description: row.description, instruction: COALESCE(row.instruction,'')})
MERGE (ItemRoot)-[r1:LATEST_DRAFT {change_description:'Initial', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(ItemValue)
MERGE (ItemRoot)-[r2:LATEST]->(ItemValue)
MERGE (ItemRoot)-[r3:HAS_DESCRIPTION]->(DescriptionRoot)
MERGE (DescriptionRoot)-[r4:LATEST_DRAFT {change_description:'Initial', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(DescriptionValue)
MERGE (Library)-[r5:CONTAINS_CONCEPT]->(DescriptionRoot)
MERGE (DescriptionRoot)-[r6:LATEST]->(DescriptionValue);

// Script to create the relationship between Item and Codelist when applicable
LOAD CSV WITH HEADERS FROM 'file:///odm_items.csv' AS row
WITH row
WHERE row.codelist IS NOT NULL
MATCH (CodelistRoot:CTCodelistRoot {uid: row.codelist})
MATCH (ItemRoot:OdmItemRoot {uid: row.oid})
MERGE (ItemRoot)-[r4:HAS_CODELIST]->(CodelistRoot);

// Script to create the relationship between Item and Unit when applicable
LOAD CSV WITH HEADERS FROM 'file:///odm_items.csv' AS row
WITH row
WHERE row.unit IS NOT NULL
MATCH (UnitRoot:UnitDefinitionRoot)-[r1:LATEST]->(UnitDefinitionValue:UnitDefinitionValue {name: row.unit})
MATCH (ItemRoot:OdmItemRoot {uid: row.oid})
MERGE (ItemRoot)-[r4:HAS_UNIT_DEFINITION]->(UnitRoot);

// Script to create the relationship between Forms and ItemGroups
LOAD CSV WITH HEADERS FROM 'file:///odm_forms_to_itemgroups.csv' AS row
MATCH (FormRoot:OdmFormRoot {uid: row.uid_form})-[r1:LATEST]->(FormValue:OdmFormValue)
MATCH (ItemGroupRoot:OdmItemGroupRoot {uid: row.uid_itemgroup})-[r2:LATEST]->(ItemGroupValue:OdmItemGroupValue)
MERGE (ItemGroupRoot)<-[r4:ITEM_GROUP_REF {order_number: row.order_number, mandatory: row.mandatory, collection_exception_condition: COALESCE(row.collection_exception_condition_oid, '')}]-(FormRoot);

// Script to create the relationship between ItemGroups and Items
LOAD CSV WITH HEADERS FROM 'file:///odm_itemgroups_to_items.csv' AS row
MATCH (ItemGroupRoot:OdmItemGroupRoot {uid: row.uid_itemgroup})-[r1:LATEST]->(ItemGroupValue:OdmItemGroupValue)
MATCH (ItemRoot:OdmItemRoot {uid: row.uid_item})-[r2:LATEST]->(ItemValue:OdmItemValue)
MERGE (ItemRoot)<-[r4:ITEM_REF {order_number: row.order_number, mandatory: row.mandatory, collection_exception_condition: COALESCE(row.collection_exception_condition_oid, '')}]-(ItemGroupRoot);

// Script to link Form with ActivityGroup (ActivityGroup)
LOAD CSV WITH HEADERS FROM 'file:///odm_forms_to_activitygroup.csv' AS row
MATCH (FormRoot:OdmFormRoot {uid: row.uid_form})-[r1:LATEST]->(FormValue:OdmFormValue)
MATCH (ActivityGroupRoot:ActivityGroupRoot)-[r2:LATEST]->(ActivityGroupValue:ActivityGroupValue {name: row.name_activitygroup})
MERGE (FormRoot)-[r4:HAS_ACTIVITY_GROUP {order_number: row.order_number}]->(ActivityGroupRoot);

// Script to link Item Group with ActivitySubGroup (ActivitySubGroup)
LOAD CSV WITH HEADERS FROM 'file:///odm_itemgroups_to_activitysubgroup.csv' AS row
MATCH (ItemGroupRoot:OdmItemGroupRoot {uid: row.uid_itemgroup})-[r1:LATEST]->(ItemGroupValue:OdmItemGroupValue)
MATCH (ActivitySubGroupRoot:ActivitySubGroupRoot)-[r2:LATEST]->(ActivitySubGroupValue:ActivitySubGroupValue {name: row.name_activitysubgroup})
MERGE (ItemGroupRoot)-[r4:HAS_ACTIVITY_SUB_GROUP {order_number: row.order_number}]->(ActivitySubGroupRoot);

// Script to link Item with Activity
LOAD CSV WITH HEADERS FROM 'file:///odm_items_to_assessments.csv' AS row
MATCH (ItemRoot:OdmItemRoot {uid: row.uid_item})-[r1:LATEST]->(ItemValue:OdmItemValue)
MATCH (ActivityRoot:ActivityRoot)-[r2:LATEST]->(ActivityValue:ActivityValue {name: row.name_assessment})
MERGE (ItemRoot)-[r4:HAS_ACTIVITY {order_number: row.order_number}]->(ActivityRoot);

-----------------------------------------------------------------------------------

// Script to display the Forms, ItemGroups and Items
//ODM metadata
MATCH (n1:OdmFormRoot)-[r1]->(n2:OdmFormValue)
WHERE n1.uid IN ['F.DM']
OPTIONAL MATCH (n1)-[r2:ITEM_GROUP_REF]->(n3:OdmItemGroupRoot)-[r3]->(n4:OdmItemGroupValue)
OPTIONAL MATCH (n3)-[r4:ITEM_REF]->(n5:OdmItemRoot)-[r5]->(n6:OdmItemValue)
OPTIONAL MATCH (n5)-[r6:HAS_UNIT_DEFINITION]->(n7)-[r7]->(n8:UnitDefinitionValue)
OPTIONAL MATCH (n5)-[r8:HAS_CODELIST]->(n9:CTCodelistRoot)-[r9:HAS_TERM]->(n10:CTTermRoot)-[r10:HAS_ATTRIBUTES_ROOT]->(n11:CTTermAttributesRoot)-[r11]->(n12:CTTermAttributesValue)
OPTIONAL MATCH (n1)-[r12:HAS_ACTIVITY_GROUP]->(n13:ActivityGroupRoot)-[r14]->(n14:ActivityGroupValue)
OPTIONAL MATCH (n3)-[r15:HAS_ACTIVITY_SUB_GROUP]->(n15:ActivitySubGroupRoot)-[r16]->(n16:ActivitySubGroupValue)
OPTIONAL MATCH (n5)-[r17:HAS_ACTIVITY]->(n17:ActivityRoot)-[r18]->(n18:ActivityValue)
OPTIONAL MATCH (n18)<-[r19:IN_HIERARCHY]-(n19:ActivityInstanceValue)
RETURN n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, n16, n17, n18, n19;

// Script to display the Form, the ItemGroups and Item for a dedicated Form
MATCH (n2:OdmFormRoot)-[r2:LATEST]->(n3:OdmFormValue)<-[r3:ITEM_GROUP_REF]-(n4:OdmItemGroupValue)<-[r4:ITEM_REF]-(n5:OdmItemValue)
WHERE n2.uid = 'F.DM'
OPTIONAL MATCH (n4)-[r7:HAS_UNIT_DEFINITION]->(n8)-[r8:LATEST]->(n9:UnitDefinitionValue)
OPTIONAL MATCH (n4)-[r5:HAS_CODELIST]->(n6:CTCodelistRoot)-[r6:HAS_TERM]->(n7:CTTermRoot)
RETURN n3, n4, n5, n6, n7, n8, n9;

// Script to display the Form, the ItemGroups and Item for a dedicated Form (V2)
MATCH (n2:OdmFormRoot)-[r2:LATEST]->(n3:OdmFormValue)<-[r3:ITEM_GROUP_REF]-(n4:OdmItemGroupValue)<-[r4:ITEM_REF]-(n5:OdmItemValue)
WHERE n2.uid = 'F.DM'
OPTIONAL MATCH (n5)-[r5:HAS_CODELIST]->(n6:CTCodelistRoot)-[r6:HAS_TERM]->(n7:CTTermRoot)
OPTIONAL MATCH (n5)-[r7:HAS_UNIT_DEFINITION]->(n8)-[r8:LATEST]->(n9:UnitDefinitionValue)
RETURN n3, n4, n5, n6, n7, n8, n9;

// Script to DELETE every metadata dealing with Forms, ItemGroups and Items... CAUTION
MATCH (o:OdmDescriptionRoot) DETACH DELETE o;
MATCH (o:OdmDescriptionValue) DETACH DELETE o;
MATCH (o:OdmDescriptionCounter) DETACH DELETE o;
MATCH (o:OdmAliasRoot) DETACH DELETE o;
MATCH (o:OdmAliasValue) DETACH DELETE o;
MATCH (o:OdmAliasCounter) DETACH DELETE o;
MATCH (o:OdmFormRoot) DETACH DELETE o;
MATCH (o:OdmFormValue) DETACH DELETE o;
MATCH (o:OdmFormCounter) DETACH DELETE o;
MATCH (o:OdmItemGroupRoot) DETACH DELETE o;
MATCH (o:OdmItemGroupValue) DETACH DELETE o;
MATCH (o:OdmItemGroupCounter) DETACH DELETE o;
MATCH (o:OdmItemRoot) DETACH DELETE o;
MATCH (o:OdmItemValue) DETACH DELETE o;
MATCH (o:OdmItemCounter) DETACH DELETE o;
MATCH (o:OdmTemplateRoot) DETACH DELETE o;
MATCH (o:OdmTemplateValue) DETACH DELETE o;
MATCH (o:OdmTemplateCounter) DETACH DELETE o;
MATCH (o:OdmConditionRoot) DETACH DELETE o;
MATCH (o:OdmConditionValue) DETACH DELETE o;
MATCH (o:OdmConditionCounter) DETACH DELETE o;
MATCH (o:OdmFormalExpressionRoot) DETACH DELETE o;
MATCH (o:OdmFormalExpressionValue) DETACH DELETE o;
MATCH (o:OdmFormalExpressionCounter) DETACH DELETE o;
MATCH (s:SdtmVariableRoot) DETACH DELETE s;
MATCH (s:SdtmVariableValue) DETACH DELETE s;
MATCH (s:SdtmVariableCounter) DETACH DELETE s;