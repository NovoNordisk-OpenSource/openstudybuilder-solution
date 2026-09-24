//Data Exchange Metadata for the study

call apoc.when(size($neodash_activitygroupvalue_name)>0,"MATCH (:StudyRoot {uid:$a})-[:LATEST]->(s:StudyValue)-->(visit:StudyVisit)-->(schedule:StudyActivitySchedule)<--(s_act:StudyActivity)-->(:StudyActivitySubGroup)-->(p_asgrp:ActivitySubGroupValue)-->(sg:ActivityValidGroup)-->(p_agrp:ActivityGroupValue) where p_agrp.name in $b
MATCH (s_act)-->(p_act:ActivityValue)-[:HAS_GROUPING]->(g:ActivityGrouping)<-[:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)<--(s_ai:StudyActivityInstance)<--()-->(visit)-[:HAS_VISIT_NAME]->(x)-[:LATEST]->(visit_name),(visit)-[:HAS_STUDY_DURATION_DAYS]->(y)-[:LATEST]->(visitdy), (visit)-->(schedule)  
MATCH (s)-[:HAS_STUDY_ACTIVITY_INSTANCE]->(s_ai)-[:HAS_ITEM]->(s_aitm1:StudyActivityItem)
MATCH (s)-[:HAS_STUDY_EPOCH]->(epoch)-[:STUDY_EPOCH_HAS_STUDY_VISIT]->(visit),(epoch)-[:HAS_EPOCH]->(ct_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(ct_attrib_root)-[:LATEST]->(epoch_term) 
WITH DISTINCT s,p_agrp, p_asgrp, visit,visit_name,visitdy,p_act,p_ai,epoch_term, s_aitm1
OPTIONAL MATCH (p_ai)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) 
OPTIONAL MATCH (p_ai)-[:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[:LATEST]->(p_aic:ActivityInstanceClassValue)  
MATCH (p_aitm1)<-[:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[:LATEST]->(p_aitmc1:ActivityItemClassValue) 
MATCH (visit)-[:STUDY_VISIT_HAS_SCHEDULE]->(schedule)-[:STUDY_ACTIVITY_SCHEDULE_HAS_CONTRACT]->(dc:StudyDataContract)<-[:STUDY_ACTIVITY_ITEM_HAS_CONTRACT]-(s_aitm1)<-[:HAS_SELECTED_ACTIVITY_ITEM]-(p_aitm1)
OPTIONAL MATCH (s_aitm1)<-[:HAS_ITEM]-(sss:StudySourceSystem)-[:HAS_SELECTED_SOURCE_SYSTEM]->(dataProvider:SourceSystem) where dataProvider.name = $c
OPTIONAL MATCH(veeva_dm:DataModelIGValue)<-[:HAS_DATA_MODEL_IG]-(sss), (veeva_dm)-[:HAS_DATASET]->(veeva_ds:DatasetInstance)-[:HAS_DATASET_VARIABLE]->(var_inst:DatasetVariableInstance)<-[:HAS_INSTANCE]-(veeva_col:DatasetVariable)<-[:HAS_DATASET_VARIABLE]-(p_aitm1),(veeva_col)<-[:HAS_DATASET_VARIABLE]-(connect:VariableConnect)-[:HAS_CONNECT_RULE]->(oak_rule:ConnectRule),(p_aitm1)-[:HAS_VARIABLE_CONNECT]->(connect) 
OPTIONAL MATCH (s_aitm1)-[:HAS_ORIGIN_TYPE]->()-->(:CTTermAttributesRoot)-[:LATEST]->(origin:CTTermAttributesValue)
OPTIONAL MATCH (p_ai)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) 
OPTIONAL MATCH (p_ai)-[:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[:LATEST]->(p_aic:ActivityInstanceClassValue)  
OPTIONAL MATCH (p_aitm1)<-[:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[:LATEST]->(p_aitmc1:ActivityItemClassValue) 
WITH DISTINCT s,p_agrp, p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitm1,p_aitmc1,p_aitmc1r, origin, dataProvider,veeva_col,connect, oak_rule
MATCH(p_dmigv:DataModelIGValue)<-[:EXTENDS_VERSION]-(mas_model:SponsorModelValue)  WHERE mas_model.name=$d
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitm1,p_aitmc1,p_aitmc1r,p_dmigv,mas_model,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(x1:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(x2:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(x3:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number}]-(x4:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(x5:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset) ,(p_aitm1_dom)-->(x6:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x7:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  WHERE p_ds.uid=p_ct2_cdisc_dom.code_submission_value
OPTIONAL MATCH (p_aitmc1r)-[:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(x8:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number, catalogue:'SDTMIG'}]-(p_dci:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(p_dsi:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds)<-[:HAS_DATASET]-(x9:DataModelCatalogue)-[:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[:CONTAINS_DATA_MODEL_IG]-(p_dmig) WHERE p_dmigv.version_number=p_dmigv.version_number 
OPTIONAL MATCH (p_dci)<-[:HAS_INSTANCE]-(sdtm_var:DatasetVariable)-[:HAS_INSTANCE]->(mas_var:SponsorModelDatasetVariableInstance)<-[:HAS_DATASET_VARIABLE]-(mas_ds:SponsorModelDatasetInstance)<-[:HAS_INSTANCE]-(p_ds)
OPTIONAL match (p_aitm1)-[:HAS_CT_TERM]->(y:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x10:CTTermAttributesRoot)-[:LATEST]->(term) 
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1, p_varcl,p_dci,p_dsi,p_ds, p_unitdefr,sdtm_var,mas_var,mas_ds,mas_model, origin, dataProvider,veeva_col,connect, oak_rule,
CASE WHEN p_unitdefr is not null THEN p_unitdef.name ELSE CASE WHEN p_varcl.uid='--TEST' THEN term.preferred_term ELSE term.code_submission_value END END as terms
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi,p_ds, p_unitdefr,sdtm_var,mas_var,mas_ds,mas_model,terms,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST_FINAL]->(p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(l:CTTermRoot)-->(z:CTTermNameRoot)-[:LATEST_FINAL]->(dimension:CTTermNameValue) where p_unitdef.name in terms 
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi, p_unitdefr,p_ds,sdtm_var,mas_var,mas_ds,mas_model,terms,dimension,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH(dimension)<-[:LATEST_FINAL]-(x:CTTermNameRoot)<--(y:CTTermRoot)<-[:HAS_CT_DIMENSION]-(pos_val:UnitDefinitionValue{convertible_unit: true})<-[:LATEST_FINAL]-(v) 
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi, p_ds,sdtm_var,mas_var,mas_ds,mas_model,terms,dimension,origin, dataProvider,veeva_col,connect, oak_rule,
CASE WHEN p_unitdefr is not null THEN  pos_val.name END as units_allow
WITH DISTINCT CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as  study,
visit.short_visit_label AS visit,
toInteger(visit.visit_number) as visitnum,
toInteger(visitdy.value) as visitdy,
p_act.name AS parameter_in_protocol, 
p_ai.name as activity_instance,
veeva_col.uid as veeva_col,
connect.target_relationship as target_relationship,
oak_rule.name as oak_rule,
p_agrp.name as cat,
p_asgrp.name as scat,  
p_ai.topic_code AS topic_code,
p_ai.molecular_weight as molecular_weight,
p_aitmc1.name as activity_item_class,
origin.code_submission_value as origin,
dataProvider.name as dataProvider,
dc.uid as dataContract, 
p_varcl.uid as var_class, 
sdtm_var.uid as sdtm_var,
mas_model.name as master_model,  
mas_var.label as sdtm_var_label, 
p_ds.uid as sdtm_dataset, 
mas_ds.extended_domain as mastermodel_dataset,
mas_ds.label as sdtm_dataset_label, 
p_aitmc1.order as item_order ,
collect(distinct terms) as terms, 
epoch_term.code_submission_value as epoch,
apoc.text.join(collect(distinct units_allow),',') as alt_units where not p_aitmc1.name = 'unit_dimension'
RETURN distinct study, visit,visitnum, visitdy, parameter_in_protocol,activity_instance,topic_code, activity_item_class,veeva_col,target_relationship,oak_rule, origin, dataProvider,dataContract,var_class,
terms,sdtm_var, sdtm_var_label, sdtm_dataset, master_model, mastermodel_dataset,sdtm_dataset_label,epoch ORDER BY topic_code, visitnum",
"MATCH (:StudyRoot {uid:$a})-[:LATEST]->(s:StudyValue)-->(visit:StudyVisit)-->(schedule:StudyActivitySchedule)<--(s_act:StudyActivity)-->(:StudyActivitySubGroup)-->(p_asgrp:ActivitySubGroupValue)-->(sg:ActivityValidGroup)-->(p_agrp:ActivityGroupValue)
MATCH (s_act)-->(p_act:ActivityValue)-[:HAS_GROUPING]->(g:ActivityGrouping)<-[:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)<--(s_ai:StudyActivityInstance)<--()-->(visit)-[:HAS_VISIT_NAME]->(x)-[:LATEST]->(visit_name),(visit)-[:HAS_STUDY_DURATION_DAYS]->(y)-[:LATEST]->(visitdy), (visit)-->(schedule)  
MATCH (s)-[:HAS_STUDY_ACTIVITY_INSTANCE]->(s_ai)-[:HAS_ITEM]->(s_aitm1:StudyActivityItem)
MATCH (s)-[:HAS_STUDY_EPOCH]->(epoch)-[:STUDY_EPOCH_HAS_STUDY_VISIT]->(visit),(epoch)-[:HAS_EPOCH]->(ct_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(ct_attrib_root)-[:LATEST]->(epoch_term) 
WITH DISTINCT s,p_agrp, p_asgrp, visit,visit_name,visitdy,p_act,p_ai,epoch_term, s_aitm1
OPTIONAL MATCH (p_ai)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) 
OPTIONAL MATCH (p_ai)-[:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[:LATEST]->(p_aic:ActivityInstanceClassValue)  
MATCH (p_aitm1)<-[:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[:LATEST]->(p_aitmc1:ActivityItemClassValue) 
MATCH (visit)-[:STUDY_VISIT_HAS_SCHEDULE]->(schedule)-[:STUDY_ACTIVITY_SCHEDULE_HAS_CONTRACT]->(dc:StudyDataContract)<-[:STUDY_ACTIVITY_ITEM_HAS_CONTRACT]-(s_aitm1)<-[:HAS_SELECTED_ACTIVITY_ITEM]-(p_aitm1)
OPTIONAL MATCH (s_aitm1)<-[:HAS_ITEM]-(sss:StudySourceSystem)-[:HAS_SELECTED_SOURCE_SYSTEM]->(dataProvider:SourceSystem) where dataProvider.name = $c
OPTIONAL MATCH(veeva_dm:DataModelIGValue)<-[:HAS_DATA_MODEL_IG]-(sss), (veeva_dm)-[:HAS_DATASET]->(veeva_ds:DatasetInstance)-[:HAS_DATASET_VARIABLE]->(var_inst:DatasetVariableInstance)<-[:HAS_INSTANCE]-(veeva_col:DatasetVariable)<-[:HAS_DATASET_VARIABLE]-(p_aitm1),(veeva_col)<-[:HAS_DATASET_VARIABLE]-(connect:VariableConnect)-[:HAS_CONNECT_RULE]->(oak_rule:ConnectRule),(p_aitm1)-[:HAS_VARIABLE_CONNECT]->(connect) 
OPTIONAL MATCH (s_aitm1)-[:HAS_ORIGIN_TYPE]->()-->(:CTTermAttributesRoot)-[:LATEST]->(origin:CTTermAttributesValue)
OPTIONAL MATCH (p_ai)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) 
OPTIONAL MATCH (p_ai)-[:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[:LATEST]->(p_aic:ActivityInstanceClassValue)  
OPTIONAL MATCH (p_aitm1)<-[:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[:LATEST]->(p_aitmc1:ActivityItemClassValue) 
WITH DISTINCT s,p_agrp, p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitm1,p_aitmc1,p_aitmc1r, origin, dataProvider,veeva_col,connect, oak_rule
MATCH(p_dmigv:DataModelIGValue)<-[:EXTENDS_VERSION]-(mas_model:SponsorModelValue)  WHERE mas_model.name=$d
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitm1,p_aitmc1,p_aitmc1r,p_dmigv,mas_model,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(x1:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(x2:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(x3:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number}]-(x4:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(x5:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset) ,(p_aitm1_dom)-->(x6:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x7:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  WHERE p_ds.uid=p_ct2_cdisc_dom.code_submission_value
OPTIONAL MATCH (p_aitmc1r)-[:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(x8:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number, catalogue:'SDTMIG'}]-(p_dci:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(p_dsi:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds)<-[:HAS_DATASET]-(x9:DataModelCatalogue)-[:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[:CONTAINS_DATA_MODEL_IG]-(p_dmig) WHERE p_dmigv.version_number=p_dmigv.version_number 
OPTIONAL MATCH (p_dci)<-[:HAS_INSTANCE]-(sdtm_var:DatasetVariable)-[:HAS_INSTANCE]->(mas_var:SponsorModelDatasetVariableInstance)<-[:HAS_DATASET_VARIABLE]-(mas_ds:SponsorModelDatasetInstance)<-[:HAS_INSTANCE]-(p_ds)
OPTIONAL match (p_aitm1)-[:HAS_CT_TERM]->(y:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x10:CTTermAttributesRoot)-[:LATEST]->(term) 
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1, p_varcl,p_dci,p_dsi,p_ds, p_unitdefr,sdtm_var,mas_var,mas_ds,mas_model, origin, dataProvider,veeva_col,connect, oak_rule,
CASE WHEN p_unitdefr is not null THEN p_unitdef.name ELSE CASE WHEN p_varcl.uid='--TEST' THEN term.preferred_term ELSE term.code_submission_value END END as terms
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi,p_ds, p_unitdefr,sdtm_var,mas_var,mas_ds,mas_model,terms,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST_FINAL]->(p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(l:CTTermRoot)-->(z:CTTermNameRoot)-[:LATEST_FINAL]->(dimension:CTTermNameValue) where p_unitdef.name in terms 
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi, p_unitdefr,p_ds,sdtm_var,mas_var,mas_ds,mas_model,terms,dimension,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH(dimension)<-[:LATEST_FINAL]-(x:CTTermNameRoot)<--(y:CTTermRoot)<-[:HAS_CT_DIMENSION]-(pos_val:UnitDefinitionValue{convertible_unit: true})<-[:LATEST_FINAL]-(v) 
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi, p_ds,sdtm_var,mas_var,mas_ds,mas_model,terms,dimension,origin, dataProvider,veeva_col,connect, oak_rule,
CASE WHEN p_unitdefr is not null THEN  pos_val.name END as units_allow
WITH DISTINCT CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as  study,
visit.short_visit_label AS visit,
toInteger(visit.visit_number) as visitnum,
toInteger(visitdy.value) as visitdy,
p_act.name AS parameter_in_protocol, 
p_ai.name as activity_instance,
veeva_col.uid as veeva_col,
connect.target_relationship as target_relationship,
oak_rule.name as oak_rule,
p_agrp.name as cat,
p_asgrp.name as scat,  
p_ai.topic_code AS topic_code,
p_ai.molecular_weight as molecular_weight,
p_aitmc1.name as activity_item_class,
origin.code_submission_value as origin,
dataProvider.name as dataProvider,
dc.uid as dataContract, 
p_varcl.uid as var_class, 
sdtm_var.uid as sdtm_var,
mas_model.name as master_model,  
mas_var.label as sdtm_var_label, 
p_ds.uid as sdtm_dataset, 
mas_ds.extended_domain as mastermodel_dataset,
mas_ds.label as sdtm_dataset_label, 
p_aitmc1.order as item_order ,
collect(distinct terms) as terms, 
epoch_term.code_submission_value as epoch,
apoc.text.join(collect(distinct units_allow),',') as alt_units where not p_aitmc1.name = 'unit_dimension'
RETURN distinct study, visit,visitnum, visitdy, parameter_in_protocol,activity_instance,topic_code, activity_item_class,veeva_col,target_relationship,oak_rule, origin, dataProvider,dataContract,var_class,
terms,sdtm_var, sdtm_var_label, sdtm_dataset, master_model, mastermodel_dataset,sdtm_dataset_label,epoch ORDER BY topic_code, visitnum",{a:$neodash_studyroot_uid,b:$neodash_activitygroupvalue_name,c:$neodash_sourcesystem_name,d:$neodash_sponsormodelvalue_name}) YIELD value
return
value.study as `Trial ID`, 
value.visit as Visit,
value.visitnum as `Visit Num`, 
value.visitdy as `Visit Day`, 
value.parameter_in_protocol as `SoA Activity`,
value.activity_instance as `Activity Instance`,
value.topic_code as TopicCode, 
value.activity_item_class as ItemClass,
value.veeva_col as SourceColumn,
value.target_relationship as TargetRel,
value.oak_rule as OakRule, 
value.dataProvider as SourceModel,
value.dataContract as DataContract,
value.var_class as ClassVariable,
value.terms as Terms,
value.sdtm_var as TargetColumn, 
value.sdtm_dataset as TargetTable, 
value.master_model as SponsorTargetModel, 
value.mastermodel_dataset as SposorTargetTable,
value.epoch as Epoch ORDER BY TopicCode, `Visit Num`


:param a=>'Study_000008';
:param b=>['Vital Signs'];
:param c=>'NN Veeva EDC system';
:param d=>'sdtmig_mastermodel_3.2_NN15';

WITH DISTINCT s,p_agrp, p_asgrp, visit,visit_name,visitdy,p_act,p_ai,epoch_term, s_aitm1




OPTIONAL MATCH (s_aitm1)-[:HAS_ORIGIN_TYPE]->()-->(:CTTermAttributesRoot)-[:LATEST]->(origin:CTTermAttributesValue)
OPTIONAL MATCH (p_ai)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) 
OPTIONAL MATCH (p_ai)-[:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[:LATEST]->(p_aic:ActivityInstanceClassValue)  
OPTIONAL MATCH (p_aitm1)<-[:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[:LATEST]->(p_aitmc1:ActivityItemClassValue) 
WITH DISTINCT s,p_agrp, p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitm1,p_aitmc1,p_aitmc1r, origin, dataProvider,veeva_col,connect, oak_rule
MATCH(p_dmigv:DataModelIGValue)<-[:EXTENDS_VERSION]-(mas_model:SponsorModelValue)  WHERE mas_model.name=$d
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitm1,p_aitmc1,p_aitmc1r,p_dmigv,mas_model,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(x1:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(x2:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(x3:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number}]-(x4:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(x5:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset) ,(p_aitm1_dom)-->(x6:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x7:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  WHERE p_ds.uid=p_ct2_cdisc_dom.code_submission_value
OPTIONAL MATCH (p_aitmc1r)-[:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(x8:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number, catalogue:'SDTMIG'}]-(p_dci:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(p_dsi:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds)<-[:HAS_DATASET]-(x9:DataModelCatalogue)-[:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[:CONTAINS_DATA_MODEL_IG]-(p_dmig) WHERE p_dmigv.version_number=p_dmigv.version_number 
OPTIONAL MATCH (p_dci)<-[:HAS_INSTANCE]-(sdtm_var:DatasetVariable)-[:HAS_INSTANCE]->(mas_var:SponsorModelDatasetVariableInstance)<-[:HAS_DATASET_VARIABLE]-(mas_ds:SponsorModelDatasetInstance)<-[:HAS_INSTANCE]-(p_ds)
OPTIONAL match (p_aitm1)-[:HAS_CT_TERM]->(y:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x10:CTTermAttributesRoot)-[:LATEST]->(term) 
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1, p_varcl,p_dci,p_dsi,p_ds, p_unitdefr,sdtm_var,mas_var,mas_ds,mas_model, origin, dataProvider,veeva_col,connect, oak_rule,
CASE WHEN p_unitdefr is not null THEN p_unitdef.name ELSE CASE WHEN p_varcl.uid='--TEST' THEN term.preferred_term ELSE term.code_submission_value END END as terms
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi,p_ds, p_unitdefr,sdtm_var,mas_var,mas_ds,mas_model,terms,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST_FINAL]->(p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(l:CTTermRoot)-->(z:CTTermNameRoot)-[:LATEST_FINAL]->(dimension:CTTermNameValue) where p_unitdef.name in terms 
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi, p_unitdefr,p_ds,sdtm_var,mas_var,mas_ds,mas_model,terms,dimension,origin, dataProvider,veeva_col,connect, oak_rule
OPTIONAL MATCH(dimension)<-[:LATEST_FINAL]-(x:CTTermNameRoot)<--(y:CTTermRoot)<-[:HAS_CT_DIMENSION]-(pos_val:UnitDefinitionValue{convertible_unit: true})<-[:LATEST_FINAL]-(v) 
WITH DISTINCT s,p_agrp,p_asgrp,visit,visit_name,visitdy,p_act,p_ai,dc,epoch_term,p_aitmc1,p_varcl,p_dci,p_dsi, p_ds,sdtm_var,mas_var,mas_ds,mas_model,terms,dimension,origin, dataProvider,veeva_col,connect, oak_rule,
CASE WHEN p_unitdefr is not null THEN  pos_val.name END as units_allow
WITH DISTINCT CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as  study,
visit.short_visit_label AS visit,
toInteger(visit.visit_number) as visitnum,
toInteger(visitdy.value) as visitdy,
p_act.name AS parameter_in_protocol, 
p_ai.name as activity_instance,
veeva_col.uid as veeva_col,
connect.target_relationship as target_relationship,
oak_rule.name as oak_rule,
p_agrp.name as cat,
p_asgrp.name as scat,  
p_ai.topic_code AS topic_code,
p_ai.molecular_weight as molecular_weight,
p_aitmc1.name as activity_item_class,
origin.code_submission_value as origin,
dataProvider.name as dataProvider,
dc.uid as dataContract, 
p_varcl.uid as var_class, 
sdtm_var.uid as sdtm_var,
mas_model.name as master_model,  
mas_var.label as sdtm_var_label, 
p_ds.uid as sdtm_dataset, 
mas_ds.extended_domain as mastermodel_dataset,
mas_ds.label as sdtm_dataset_label, 
p_aitmc1.order as item_order ,
collect(distinct terms) as terms, 
epoch_term.code_submission_value as epoch,
apoc.text.join(collect(distinct units_allow),',') as alt_units where not p_aitmc1.name = 'unit_dimension'
RETURN distinct study, visit,visitnum, visitdy, parameter_in_protocol,activity_instance,topic_code, activity_item_class,veeva_col,target_relationship,oak_rule, origin, dataProvider,dataContract,var_class,
terms,sdtm_var, sdtm_var_label, sdtm_dataset, master_model, mastermodel_dataset,sdtm_dataset_label,epoch ORDER BY topic_code, visitnum




//NEW
MATCH (:StudyRoot {uid:$a})-[:LATEST]->(s:StudyValue)-->(visit:StudyVisit)-->(schedule:StudyActivitySchedule)<--(s_act:StudyActivity)-->(:StudyActivitySubGroup)-->(p_asgrp:ActivitySubGroupValue)-->(sg:ActivityValidGroup)-->(p_agrp:ActivityGroupValue)
MATCH (s_act)-->(p_act:ActivityValue)-[:HAS_GROUPING]->(g:ActivityGrouping)<-[:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)<--(s_ai:StudyActivityInstance)<--()-->(visit)-[:HAS_VISIT_NAME]->(x)-[:LATEST]->(visit_name),(visit)-[:HAS_STUDY_DURATION_DAYS]->(y)-[:LATEST]->(visitdy), (visit)-->(schedule)-[:STUDY_ACTIVITY_SCHEDULE_HAS_CONTRACT]->(dc:StudyDataContract)<-[:STUDY_ACTIVITY_ITEM_HAS_CONTRACT]-(s_aitm1:StudyActivityItem)<-[:HAS_SELECTED_ACTIVITY_ITEM]-(p_aitm1:ActivityItem)<-[:CONTAINS_ACTIVITY_ITEM]-(p_ai) 
MATCH (s)-[:HAS_STUDY_EPOCH]->(epoch)-[:STUDY_EPOCH_HAS_STUDY_VISIT]->(visit),(epoch)-[:HAS_EPOCH]->(ct_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(ct_attrib_root)-[:LATEST]->(epoch_term)
MATCH (p_aitm1)<-[:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[:LATEST]->(p_aitmc1:ActivityItemClassValue) 
OPTIONAL MATCH (s_aitm1)<-[:HAS_ITEM]-(sss:StudySourceSystem)-[:HAS_SELECTED_SOURCE_SYSTEM]->(dataProvider:SourceSystem) where dataProvider.name = $c
OPTIONAL MATCH(veeva_dm:DataModelIGValue)<-[:HAS_DATA_MODEL_IG]-(sss), (veeva_dm)-[:HAS_DATASET]->(veeva_ds:DatasetInstance)-[:HAS_DATASET_VARIABLE]->(var_inst:DatasetVariableInstance)<-[:HAS_INSTANCE]-(veeva_col:DatasetVariable)<-[:HAS_DATASET_VARIABLE]-(p_aitm1),(veeva_col)<-[:HAS_DATASET_VARIABLE]-(connect:VariableConnect)-[:HAS_CONNECT_RULE]->(oak_rule:ConnectRule),(p_aitm1)-[:HAS_VARIABLE_CONNECT]->(connect) 
MATCH(p_dmigv:DataModelIGValue)<-[:EXTENDS_VERSION]-(mas_model:SponsorModelValue)  WHERE mas_model.name=$d
OPTIONAL MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(x1:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(x2:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(x3:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number}]-(x4:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(x5:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset) ,(p_aitm1_dom)-->(x6:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x7:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  WHERE p_ds.uid=p_ct2_cdisc_dom.code_submission_value
OPTIONAL MATCH (p_aitmc1r)-[:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(x8:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:p_dmigv.version_number, catalogue:'SDTMIG'}]-(p_dci:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:p_dmigv.version_number}]-(p_dsi:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds)<-[:HAS_DATASET]-(x9:DataModelCatalogue)-[:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[:CONTAINS_DATA_MODEL_IG]-(p_dmig) WHERE p_dmigv.version_number=p_dmigv.version_number 
OPTIONAL MATCH (p_dci)<-[:HAS_INSTANCE]-(sdtm_var:DatasetVariable)-[:HAS_INSTANCE]->(mas_var:SponsorModelDatasetVariableInstance)<-[:HAS_DATASET_VARIABLE]-(mas_ds:SponsorModelDatasetInstance)<-[:HAS_INSTANCE]-(p_ds)
OPTIONAL match (p_aitm1)-[:HAS_CT_TERM]->(y:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(x10:CTTermAttributesRoot)-[:LATEST]->(term)
return *