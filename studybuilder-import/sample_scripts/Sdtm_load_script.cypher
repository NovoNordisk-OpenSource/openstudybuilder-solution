// Metadata: For the Domain - Datasets
// basic_std,table,column,label,order,type,length,displayformat,xmldatatype,xmlcodelist,xmlcodelist_multi,core,origin,role,term,algorithm,qualifiers,comment,IGcomment,class_table,class_column,map_var_flag,fixed_mapping,include_in_raw,nn_internal,value_lvl_where_cols,value_lvl_label_col,value_lvl_collect_ct_val,value_lvl_ct_cdlist_id_col,enrich_build_order,enrich_rule,xmlcodelistvalues
LOAD CSV WITH HEADERS FROM 'file:///sdtm_mastermodelsheet_3.2-NN14_refcolumns.csv' AS row
MATCH (Library:Library {name: 'Sponsor'})
MERGE (DomainRoot:ConceptRoot:SdtmDomainRoot {uid: row.table})
MERGE (DomainValue:ConceptValue:SdtmDomainValue {oid: row.table, name: row.table, repeating: 'No'})
MERGE (Library)-[r0:CONTAINS_CONCEPT]->(DomainRoot)
MERGE (DomainRoot)-[r2:LATEST_DRAFT {change_description:'Initial version', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(DomainValue)
MERGE (DomainRoot)-[r3:LATEST]->(DomainValue);

// Metadata: For the Variables in Datasets
// basic_std,table,column,label,order,type,length,displayformat,xmldatatype,xmlcodelist,xmlcodelist_multi,core,origin,role,term,algorithm,qualifiers,comment,IGcomment,class_table,class_column,map_var_flag,fixed_mapping,include_in_raw,nn_internal,value_lvl_where_cols,value_lvl_label_col,value_lvl_collect_ct_val,value_lvl_ct_cdlist_id_col,enrich_build_order,enrich_rule,xmlcodelistvalues
LOAD CSV WITH HEADERS FROM 'file:///sdtm_mastermodelsheet_3.2-NN14_refcolumns.csv' AS row
MATCH (DomainRoot:SdtmDomainRoot {uid: row.table})
MERGE (VariableRoot:ConceptRoot:SdtmVariableRoot {uid: row.column})
MERGE (VariableValue:ConceptValue:SdtmVariableValue {oid: row.column, name: row.lable, datatype: row.xmldatatype})
MERGE (DomainRoot)-[r2:LATEST_DRAFT {change_description:'Initial version', start_date:datetime(), status:'Draft', author_id:'ndsj', version:'0.1'}]->(VariableRoot)
MERGE (VariableRoot)-[r3:LATEST]->(DomainValue);

https://dev.azure.com/orgremoved/Clinical-MDR/_git/studybuilder?version=GB835659-crf-form-page

