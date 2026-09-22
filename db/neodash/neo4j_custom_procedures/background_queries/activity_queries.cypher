//Activity with data type and role
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name='Albumin'
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R10:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R12:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R14:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrpp) 
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
OPTIONAL MATCH(p_ct2cd)<-[R23:HAS_TERM]-(clr:CTCodelistRoot)-[R24:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot)-[R27:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH(clr)-[R25:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[R26:LATEST]-(p_cl_sponsor)
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[R28:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[R29:HAS_TERM]-(cl_root)-[R30:HAS_ATTRIBUTES_ROOT]->(clattr2)-[R31:LATEST]->(unit_cld)
OPTIONAL MATCH(p_aitmc1)-[R32:HAS_ROLE]->(p_role_r:CTTermRoot), (p_role_r)-[R33:HAS_NAME_ROOT]->(ctnr_role)-[R34:LATEST]->(p_role_val), (p_role_r)-[R35:HAS_ATTRIBUTES_ROOT]->(ctattr)-[R36:LATEST]->(p_role_attr_val)
OPTIONAL MATCH(p_aitmc1)-[R37:HAS_DATA_TYPE]->(p_dtype_r),  (p_dtype_r)-[R38:HAS_NAME_ROOT]->(ctnr_dtype)-[R39:LATEST]->(p_dtype_val), (p_dtype_r)-[R40:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[R41:LATEST]->(p_dtype_attr_val)
return distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,R1,R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43

//Activity as logical view - used in the procedures
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue) where p_act.name='Systolic Blood Pressure'
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
WITH g,p_act,p_ai,p_aicr,
apoc.create.vNode(["ActivityInstance"],properties(p_ai)) as ai,
apoc.create.vNode(["ActivityInstanceClass"],properties(p_aic)) as aic
WITH g,p_act,p_ai,p_aicr,ai,aic,
apoc.create.vRelationship(p_act,"HAS",{type:"logical"},ai) as r1,
apoc.create.vRelationship(ai,"HAS_ACTIVITY",{type:"logical"},g) as r2,
apoc.create.vRelationship(ai,"OF_CLASS",{type:"logical"},aic) as r3
with g,p_act,p_ai,p_aicr,ai,aic,r1,r2,r3
MATCH(p_act:ActivityValue)-[R3:HAS_GROUPING]->(g:ActivityGrouping)-[R4:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R5:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R6:IN_GROUP]->(p_agrp:ActivityGroupValue)
with g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,ai,aic,r1,r2,r3,R3,R4,R5,R6
MATCH (p_ai:ActivityInstanceValue)-[R7:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem)
OPTIONAL MATCH(p_aitm1)<-[R9:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R10:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R11:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R12:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R13:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R14:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R17:HAS_ITEM_CLASS]-(p_aicrpp) 
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,r1,r2,r3,p_aitm1,p_aitmc1,p_aicp,p_aicpp,R3,R4,R5,R6,R15,R16,R17,
p_aitm1 as aitm1,
apoc.create.vNode(["ActivityItemClass"],properties(p_aitmc1)) as aitmc1,
CASE WHEN R16 is not null THEN apoc.create.vNode(["ActivityInstanceClass"],properties(p_aicp)) END as aicp,
CASE WHEN R17 is not null THEN apoc.create.vNode(["ActivityInstanceClass"],properties(p_aicpp)) END as aicpp
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aitm1,p_aitmc1,ai,aic,r1,r2,r3,aitm1,aitmc1,aicp,aicpp,R3,R4,R5,R6,R15,R16,R17,
apoc.create.vRelationship(ai,"HAS",{type:"logical"},aitm1) as r4,
apoc.create.vRelationship(aitm1,"OF_CLASS",{type:"logical"},aitmc1) as r5,
CASE WHEN (R15 is not null) THEN 
apoc.create.vRelationship(aitmc1,"OF_CLASS",{type:"logical"},aic) END as r6,
CASE WHEN (R16 is not null) 
THEN apoc.create.vRelationship(aitmc1,"OF_CLASS",{type:"logical"},aicp) END as r7,
CASE WHEN (R17 is not null) 
THEN apoc.create.vRelationship(aitmc1,"OF_CLASS",{type:"logical"},aicpp) END as r8
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aitm1,p_aitmc1,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,R3,R4,R5,R6,R15,R16,R17
OPTIONAL MATCH (p_aitm1)-[R18]->(p_ct2cd:CTTermRoot)-[R19:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R20:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R21:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R22:LATEST]->(p_ct2_cdisc)
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[:LATEST]->(p_unitdef:UnitDefinitionValue)
OPTIONAL MATCH(p_aitmc1)-[:HAS_ROLE]->(p_role_r:CTTermRoot)-[:HAS_NAME_ROOT]->(ctnr_role)-[:LATEST]->(p_role_val), (p_role_r)-[:HAS_ATTRIBUTES_ROOT]->(ctattr)-[:LATEST]->(p_role_attr_val)
OPTIONAL MATCH(p_aitmc1)-[:HAS_DATA_TYPE]->(p_dtype_r)-[:HAS_NAME_ROOT]->(ctnr_dtype)-[:LATEST]->(p_dtype_val), (p_dtype_r)-[:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[:LATEST]->(p_dtype_attr_val)
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,R3,R4,R5,R6,
p_ct2cd,p_unitdefr,p_role_r,p_dtype_r,p_ct2_cdisc,p_ct2_sponsor,p_unitdef,p_role_val,p_role_attr_val,p_dtype_val,p_dtype_attr_val,
CASE WHEN p_ct2cd is not null THEN
apoc.create.vNode(["CTTerm"],apoc.map.merge(properties(p_ct2_cdisc),properties(p_ct2_sponsor))) END as ct2,
CASE WHEN p_unitdefr is not null THEN
apoc.create.vNode(["CTTerm"],properties(p_unitdef)) END as unit_ct,
CASE WHEN p_role_r is not null THEN apoc.create.vNode(["CTTerm"],apoc.map.merge(properties(p_role_val),properties(p_role_attr_val))) END as role,
CASE WHEN p_dtype_r is not null THEN apoc.create.vNode(["CTTerm"],apoc.map.merge(properties(p_dtype_val),properties(p_dtype_attr_val))) END as dtype
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,R3,R4,R5,R6,
p_ct2cd,p_unitdefr,p_role_r,p_dtype_r,p_ct2_cdisc,p_ct2_sponsor,p_unitdef,p_role_val,p_role_attr_val,p_dtype_val,p_dtype_attr_val,ct2,unit_ct,role,dtype,
CASE WHEN p_ct2cd is not null THEN
apoc.create.vRelationship(aitm1,"FOR",{type:"logical"},ct2) END as r9, 
CASE WHEN p_unitdefr is not null THEN
apoc.create.vRelationship(aitm1,"FOR",{type:"logical"},unit_ct) END as r10,
CASE WHEN p_role_r is not null THEN apoc.create.vRelationship(aitmc1,"HAS_ROLE",{type:"logical"},role)END as r11,
CASE WHEN p_dtype_r is not null THEN apoc.create.vRelationship(aitmc1,"HAS_TYPE",{type:"logical"},dtype) END as r12
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,R3,R4,R5,R6,
p_ct2cd,p_unitdefr,p_unitdef,ct2,unit_ct,role,dtype
OPTIONAL MATCH(p_ct2cd)<-[R23:HAS_TERM]-(clr:CTCodelistRoot)-[R24:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot)-[R27:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH(clr)-[R25:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[R26:LATEST]-(p_cl_sponsor)
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[:HAS_TERM]-(cl_root)-[:HAS_ATTRIBUTES_ROOT]->(clattr2)-[:LATEST]->(unit_cld)
with distinct g as g,
sg as sg,
p_agrp as p_agrp ,
p_asgrp as p_asgrp,
p_act as p_act,
p_ai as p_ai,
ai as ai,
aic as aic,
aicp as aicp,
aicpp as aicpp,
aitm1 as aitm1,
aitmc1 as aitmc1,
r1 as r1,
r2 as r2,
r3 as r3,
r4 as r4,
r5 as r5,
r6 as r6,
r7 as r7,
r8 as r8,
r9 as r9,
r10 as r10,
r11 as r11,
r12 as r12,
R3 as R3,
R4 as R4,
R5 as R5,
R6 as R6,
p_ct2cd as p_ct2cd,
p_unitdefr as p_unitdefr,
ct2 as ct2,
unit_ct as unit_ct,
role as role,
dtype as dtype,
p_cl_cdisc as p_cl_cdisc,
p_cl_sponsor as p_cl_sponsor,
unit_cld as unit_cld
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,R3,R4,R5,R6,p_ct2cd,p_unitdefr,ct2,unit_ct,role,dtype,p_cl_cdisc,p_cl_sponsor,unit_cld,
CASE WHEN p_ct2cd is not null THEN apoc.create.vNode(["CTCodeList"],apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor))) END as cl,
CASE WHEN p_unitdefr is not null THEN
apoc.create.vNode(["CTCodeList"],properties(unit_cld)) END as unit_cl
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,R3,R4,R5,R6,p_ct2cd,p_unitdefr,ct2,unit_ct,role,dtype,cl,unit_cl,
CASE WHEN p_ct2cd is not null THEN
apoc.create.vRelationship(cl,"HAS",{type:"logical"},ct2) END as r13,
CASE WHEN p_unitdefr is not null THEN
apoc.create.vRelationship(unit_ct,"HAS",{type:"logical"},unit_cl) END as r14
RETURN g,sg,p_agrp,p_asgrp,p_act,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,R3,R4,R5,R6,ct2,unit_ct,role,dtype,unit_cl,cl


//Activity as cosmos concept
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name=$neodash_cosmos_activity
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R10:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R12:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R14:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrpp) 
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
OPTIONAL MATCH(p_ct2cd)<-[R23:HAS_TERM]-(clr:CTCodelistRoot)-[R24:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot)-[R27:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH(clr)-[R25:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[R26:LATEST]-(p_cl_sponsor)
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[R28:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[R29:HAS_TERM]-(cl_root)-[R30:HAS_ATTRIBUTES_ROOT]->(clattr2)-[R31:LATEST]->(unit_cld)
OPTIONAL MATCH(p_aitmc1)-[R32:HAS_ROLE]->(p_role_r:CTTermRoot), (p_role_r)-[R33:HAS_NAME_ROOT]->(ctnr_role)-[R34:LATEST]->(p_role_val), (p_role_r)-[R35:HAS_ATTRIBUTES_ROOT]->(ctattr)-[R36:LATEST]->(p_role_attr_val)
OPTIONAL MATCH(p_aitmc1)-[R37:HAS_DATA_TYPE]->(p_dtype_r),  (p_dtype_r)-[R38:HAS_NAME_ROOT]->(ctnr_dtype)-[R39:LATEST]->(p_dtype_val), (p_dtype_r)-[R40:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[R41:LATEST]->(p_dtype_attr_val)
with distinct p_act.name as ActivityName, p_aic as aic, p_asgrp as asgrp, p_aitmc1 as aitmc1,p_ai as ai,p_unitdef as unit_ct,
        CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_ct2_cdisc),properties(p_ct2_sponsor)) END as ct2,
        CASE WHEN p_role_r is not null THEN apoc.map.merge(properties(p_role_val),properties(p_role_attr_val)) END as role,
        CASE WHEN p_dtype_r is not null THEN apoc.map.merge(properties(p_dtype_val),properties(p_dtype_attr_val)) END as dtype,
        CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor)) END as cl
        WITH distinct ActivityName,aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,cl,
        CASE WHEN aitmc1.name='concept_id' THEN ct2.concept_id ELSE 
        CASE WHEN aitmc1.name='test_name_code' THEN ct2.concept_id END END as conceptId,
        CASE WHEN aitmc1.name='domain' THEN ct2.code_submission_value END as domain
        with distinct ActivityName,aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,conceptId,domain,
        CASE when (apoc.any.property(aic,'name')='NumericFinding') THEN 'Quantitative' ELSE 
        CASE WHEN (apoc.any.property(aic,'name')='CategoricFinding') THEN 'Ordinal' ELSE 
        null END END as aiclass
        WITH  conceptId, ActivityName, aiclass, asgrp.name as asgrp,  domain,  ai.name as conceptChildNames,  ai.adam_param_code as conceptChildIds, aitmc1,unit_ct,ct2,role,dtype,
        collect(distinct(coalesce(ct2.code_submission_value,unit_ct.name))) as val_lst
        WITH conceptId, ActivityName,conceptChildNames, conceptChildIds, aiclass, asgrp,domain,aitmc1,dtype.preferred_term as dtype,apoc.coll.flatten(collect(val_lst)) as val_list,toInteger(aitmc1.order) as var_order
        with conceptId, ActivityName,conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order
        call apoc.load.json('https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C82590?include=minimal%2CinverseAssociations') yield value
        with distinct conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,value['inverseAssociations'] as class_concepts
        with conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,class_concepts,
      {PERCENTAGE:"Unit of Fraction",
      `RESPIRATORY RATE`:"Unit Respiratory Rate",
       CONCENTRATION:"Unit of Concentration",
      `U_IU Concentration`:"Unit of Concentration",
       TEMPERATURE:"Unit of Temperature",
       WEIGHT:"Unit of Weight",
       PRESSURE:"Unit of Pressure",
       FLOW:"Unit of Flow Rate",
      `VOLUMETRIC FLOW RATE`:"Unit of Volumetric Flow Rate",
      `CELL COUNT`:"Unit of Cell Count",
       LENGTH:"Unit of Length",
      `NO UNIT`:"No Unit",
       TIME:"Unit of Time",
      `BEAT RATE`:"Unit of Beat Rate"} as unit_dimension_dict
      WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,class_concepts,unit_dimension_dict,
        CASE WHEN aitmc1.name='standard_unit' THEN 'Standard Result Unit' ELSE 
        CASE WHEN aitmc1.name='unit_dimension' THEN unit_dimension_dict[apoc.text.join(val_list,'')] ELSE
        CASE WHEN aitmc1.name='test_name_code' THEN "Test Code" ELSE 
        CASE WHEN aitmc1.name contains 'category' THEN 'Category' ELSE
        CASE WHEN aitmc1.name='domain' THEN 'Submission Domain' ELSE
        CASE WHEN aitmc1.name='specimen' THEN 'Biospecimen Type' ELSE
        apoc.text.join([c in class_concepts WHERE toUpper(c.relatedName)=toUpper(aitmc1.name) | c.relatedName],'') 
        END END END END END END as aitmc1_term
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,apoc.text.replace(aitmc1_term," ","%20") as aitmc1_term
        call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+aitmc1_term+"&type=match&value=term") YIELD value
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order, value.concepts[0].code as item_concept_id,aitmc1_term
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,item_concept_id,aitmc1_term
        call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+aitmc1_term+"&type=startsWith&value=term") YIELD value
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order, item_concept_id, apoc.text.join([v in value.concepts | v.code],',') as alt_item_concept_id
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,
        CASE WHEN item_concept_id is null and not alt_item_concept_id is null THEN alt_item_concept_id ELSE  item_concept_id END as item_concept_id
        WITH conceptId, ActivityName, conceptChildNames, conceptChildIds, aiclass, asgrp,domain,dtype,aitmc1,val_list,var_order,item_concept_id,
        CASE WHEN item_concept_id='' THEN '' ELSE 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+item_concept_id END as href
        WITH distinct conceptId,ActivityName, conceptChildNames , conceptChildIds, aiclass, asgrp,  domain, aitmc1.name as aitmc1Name, apoc.text.join(collect(distinct dtype),',') as dtypes,apoc.coll.flatten(collect(val_list)) as val_list ,var_order,href,item_concept_id
       with distinct conceptId,ActivityName, conceptChildNames , conceptChildIds, aiclass, asgrp,domain,dtypes,aitmc1Name,val_list,var_order,href,item_concept_id
with distinct collect(conceptId) as conceptId, ActivityName, conceptChildNames , conceptChildIds, aiclass, asgrp, collect(domain) as domain, collect(apoc.map.fromPairs([['dtypes',dtypes],['aitmc1Name',aitmc1Name],['val_list',val_list],['var_order',var_order],['href',href],['item_concept_id',item_concept_id]])) as var_map
with conceptId, 
ActivityName, 
apoc.coll.toSet(collect(conceptChildNames)) as conceptChildNames, 
apoc.coll.toSet(collect(conceptChildIds)) as conceptChildIds , 
apoc.coll.toSet(collect(aiclass)) as aiclass, 
apoc.coll.toSet(collect(asgrp)) as asgrp, 
apoc.coll.toSet(domain) as domain,
apoc.coll.toSet(apoc.coll.flatten(collect(var_map))) as var_maps
with conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp, domain, var_maps
UNWIND var_maps as var_map
with conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp,domain,
var_map['dtypes'] as dtypes,
var_map['aitmc1Name'] as aitmc1Name,
var_map['val_list'] as val_list,
var_map['var_order'] as var_order,
var_map['href'] as href,
var_map['item_concept_id'] as item_concept_id
WITH conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp,domain,apoc.coll.toSet(collect(dtypes)) as dtypes,aitmc1Name,apoc.coll.toSet(collect(href)) as href,apoc.coll.toSet(collect(item_concept_id)) as item_concept_id, apoc.coll.toSet(apoc.coll.flatten(collect(val_list))) as val_list, var_order
WITH conceptId, ActivityName, conceptChildNames,conceptChildIds,aiclass,asgrp,domain,
collect(apoc.map.fromPairs( [
                            ['conceptId', apoc.text.join(item_concept_id,',')],
                            ['href', apoc.text.join(href,',')],
                            ['shortName', aitmc1Name],
                            ['dataType',dtypes],
                            ['exampleSet',val_list]
                            ])) as vars 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds,aiclass,asgrp,domain, vars where size(conceptId)<2
with apoc.text.join(conceptId,',') as conceptId, 
ActivityName,
apoc.text.join(conceptChildNames,',') as conceptChildNames,
apoc.text.join(conceptChildIds,',') as conceptChildIds,
apoc.text.join(aiclass,',') as aiclass, 
apoc.text.join(asgrp,',') as asgrp,
apoc.text.join(domain,',') as domain, 
vars
WITH CASE when conceptId = "" THEN 'C17998' ELSE conceptId END as conceptId,ActivityName, conceptChildNames,conceptChildIds,aiclass, asgrp,domain,vars
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?limit=100&include=minimal") YIELD value
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars, value.name as conceptName
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"/parents") YIELD value
WITH conceptId, ActivityName, conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars, conceptName,value.code as parentConceptId
CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=definitions") YIELD value 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName, parentConceptId, value, [def IN value.definitions where def.source="NCI"] as def 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName, parentConceptId, def[0]["definition"] as conceptDefinition
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName, parentConceptId,conceptDefinition
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=synonyms") YIELD value 
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName,parentConceptId,conceptDefinition,value, apoc.coll.toSet([sym IN value.synonyms where sym.source="CDISC" and sym.termType="PT"| sym.name]) as conceptSynonyms
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, apoc.coll.sortMaps(vars, '^var_order') as vars,conceptName,parentConceptId,conceptDefinition,conceptSynonyms
WITH conceptId, ActivityName,conceptChildNames,conceptChildIds, aiclass,asgrp,domain, vars,conceptName,parentConceptId,conceptDefinition,conceptSynonyms,
apoc.map.fromPairs([ 
                            ['packageDate','2020'],
                            ['packageType','bc'],
                            ['conceptId',conceptId],
                            ['href', 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+conceptId],
                            ['parentConceptId',parentConceptId],
                            ['category',asgrp],
                            ['shortName',conceptName],
                            ['activityName',ActivityName],
                            ['conceptChildrenNames',conceptChildNames],
                            ['conceptChildrenIds',conceptChildIds],
                            ['synonym',conceptSynonyms],
                            ['resultScale',aiclass],
                            ['definition',conceptDefinition],
                            ['domain',domain],
                            ['dataElementConcepts', vars]
                            ]) as activity
        return distinct activity

//Activity as cosmos SDTM specialisation
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name ='Systolic Blood Pressure'
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem),(p_ai)<-[:LATEST]-(x)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R10:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R12:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R14:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrpp) 
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
OPTIONAL MATCH(p_ct2cd)<-[R23:HAS_TERM]-(clr:CTCodelistRoot)-[R24:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot),(clr)-[R25:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[R26:LATEST]-(p_cl_sponsor),(clatt)-[R27:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[R28:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[R29:HAS_TERM]-(cl_root)-[R30:HAS_ATTRIBUTES_ROOT]->(clattr2)-[R31:LATEST]->(unit_cld)
OPTIONAL MATCH(p_aitmc1)-[R32:HAS_ROLE]->(p_role_r:CTTermRoot),(p_role_r)-[R33:HAS_NAME_ROOT]->(ctnr_role)-[R34:LATEST]->(p_role_val), (p_role_r)-[R35:HAS_ATTRIBUTES_ROOT]->(ctattr)-[R36:LATEST]->(p_role_attr_val)
OPTIONAL MATCH(p_aitmc1)-[R37:HAS_DATA_TYPE]->(p_dtype_r),(p_dtype_r)-[R38:HAS_NAME_ROOT]->(ctnr_dtype)-[R39:LATEST]->(p_dtype_val), (p_dtype_r)-[R40:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[R41:LATEST]->(p_dtype_attr_val)
WITH distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,R1,R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43
MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:'3.2'}]-(:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:'3.2'}]-(:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset),(p_aitm1_dom:ActivityItem)-[x]->(y:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(p_ct2_sponsor_dom), (y)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  where p_ds.uid=p_ct2_cdisc_dom.code_submission_value OPTIONAL MATCH(p_aitmc1r)-[R44:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(p_varcli:VariableClassInstance)
,(p_varcli)<-[R46:IMPLEMENTS_VARIABLE{version_number:'3.2'}]-(var:DatasetVariableInstance)<-[R47:HAS_DATASET_VARIABLE{version_number:'3.2'}]-(p_dsi:DatasetInstance)<-[R48:HAS_INSTANCE]-(p_ds:Dataset)<-[R49:HAS_DATASET]-(p_dmcat:DataModelCatalogue)-[R50:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[R51:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[R52:CONTAINS_DATA_MODEL_IG]-(p_dmig),(p_dmcat)-[:HAS_DATASET_VARIABLE]->(dsv:DatasetVariable)-[:HAS_INSTANCE]->(var) where p_dmigv.version_number='3.2' 
with p_ai,p_aitmc1,p_dmigv,p_ds, p_varcl,dsv,var,p_role_val,p_dtype_val,clr,p_cl_cdisc,p_cl_sponsor,p_ct2cd,p_ct2_cdisc, p_ct2_sponsor where not p_aitmc1.name in ['unit_dimension','domain']
with p_aitmc1,p_dmigv, p_ds, p_varcl,dsv,var,p_role_val,p_dtype_val,clr,p_cl_cdisc,p_cl_sponsor,p_ct2cd,p_ct2_cdisc, p_ct2_sponsor,
CASE when p_ct2cd is not NULL THEN
CASE WHEN var.role='Topic' THEN
apoc.map.fromPairs([
  ['code',p_ct2cd.concept_id],
  ['submission_value',coalesce(p_ct2_cdisc.code_submission_value,toUpper(p_ct2_sponsor.name))],
  ['shortName',p_ct2_cdisc.preferred_term]
  ]) 
  ELSE
  CASE WHEN p_varcl.uid="--TEST" THEN
  apoc.map.fromPairs([
  ['code',p_ct2cd.concept_id],
  ['submission_value',coalesce(p_ct2_cdisc.preferred_term,toUpper(p_ct2_sponsor.name))]
  ]) 
  ELSE
  apoc.map.fromPairs([
  ['code',p_ct2cd.concept_id],
  ['submission_value',coalesce(p_ct2_cdisc.code_submission_value,toUpper(p_ct2_sponsor.name))]
  ]) END
  END END as val_list
  WITH p_aitmc1,p_dmigv, p_ds, p_varcl,dsv,var,p_role_val,p_dtype_val,clr,p_cl_cdisc,p_cl_sponsor,collect(distinct val_list) as terms
  WITH p_aitmc1,p_dmigv, p_ds,p_varcl,dsv,var,p_role_val,p_dtype_val,clr, p_cl_cdisc,p_cl_sponsor,terms,
  CASE WHEN var.role='Topic' THEN apoc.text.join([p_ds.uid,dsv.uid],'.') END as source,
      CASE WHEN clr is not NULL THEN
apoc.map.fromPairs([['conceptId',clr.uid],
                   ['href','https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+clr.uid],                  ['submissionValue',coalesce(p_cl_cdisc.submission_value,toUpper(p_cl_sponsor.name))]
                   ]) END as cdlist,
CASE WHEN size(terms)=1 THEN
apoc.map.fromPairs([
                   ['conceptId',terms[0]['code']],
                   ['value',terms[0]['submission_value']]
                   ]) 
END as assignedTerms,
CASE WHEN size(terms)>1 THEN [ v in terms | v['submission_value']] END as valueList,
CASE when p_aitmc1.data_collection='Yes' THEN 'Collected' ELSE 'Not Collected' END as collected
WITH p_aitmc1,p_dmigv, p_ds,p_varcl,dsv,var,p_role_val,p_dtype_val,assignedTerms, valueList,cdlist,source,terms,
CASE WHEN assignedTerms is not null THEN
        CASE WHEN var.role='Topic' and dsv.uid=cdlist['submissionValue'] THEN
          apoc.map.fromPairs( [
                                ['name', dsv.uid],
                                ['isNonStandard',false],
                                ['role',var.role],
                                ['dataType', var.simple_datatype],
                                ['codelist',cdlist],
                                ['AssignedTerm',assignedTerms],
                                ['originType', collected],
                                ['mandatoryVariable', p_aitmc1.mandatory],
                                ['mandatoryValue', p_aitmc1.mandatory]
                                ]) 
        ELSE
        CASE WHEN p_varcl.uid='--TEST' and dsv.uid=cdlist['submissionValue'] THEN
            apoc.map.fromPairs( [
                                ['name', dsv.uid],
                                ['isNonStandard',false],
                                ['role',var.role],
                                ['dataType', var.simple_datatype],
                                ['codelist',cdlist],
                                ['AssignedTerm',assignedTerms],
                                ['originType', collected],
                                ['mandatoryVariable', p_aitmc1.mandatory],
                                ['mandatoryValue', p_aitmc1.mandatory]
                                ]) 
        ELSE  
            CASE WHEN not p_varcl.uid contains 'TEST'  THEN 
               apoc.map.fromPairs( [
                                ['name', dsv.uid],
                                ['dataElementConceptId',p_aitmc1.nci_concept_id],
                                ['isNonStandard',false],
                                ['role',var.role],
                                ['dataType', var.simple_datatype],
                                ['codelist',cdlist],
                                ['AssignedTerm',assignedTerms],
                                ['originType', collected],
                                ['mandatoryVariable', p_aitmc1.mandatory],
                                ['mandatoryValue', p_aitmc1.mandatory]
                                ]) END
        END END
    ELSE
        CASE WHEN valueList is not null THEN 
            apoc.map.fromPairs( [
            ['name', dsv.uid],
            ['dataElementConceptId',p_aitmc1.nci_concept_id],
            ['isNonStandard',false],
            ['codelist',cdlist],
            ['valueList', valueList],
            ['subsetCodelist',p_dtype_val.name],
            ['role',var.role],
            ['originType', collected],
            ['mandatoryVariable', p_aitmc1.mandatory],
            ['mandatoryValue', p_aitmc1.mandatory]
            ]) 
        ELSE   
            apoc.map.fromPairs( [
            ['name', dsv.uid],
            ['dataElementConceptId',p_aitmc1.nci_concept_id],
            ['isNonStandard',false],
            ['role',var.role],
            ['dataType', var.simple_datatype],
            ['codelist',cdlist],
            ['valueList', valueList],
            ['subsetCodelist',p_dtype_val.name],
            ['originType', collected],
            ['mandatoryVariable', p_aitmc1.mandatory],
            ['mandatoryValue', p_aitmc1.mandatory]
            ]) 
END
    END as dataElement,
CASE WHEN var.role='Topic' THEN assignedTerms['conceptId'] END as biomedicalConceptId,
CASE WHEN var.role='Topic' THEN assignedTerms['value'] END as datasetSpecializationId,
CASE WHEN var.role='Topic' THEN [ v in terms | v['shortName']][0] END as shortName  
WITH apoc.coll.toSet(collect(shortName))[0] as shortName,p_dmigv, p_ds,apoc.coll.toSet(collect(source))[0] as source,apoc.coll.toSet(collect(biomedicalConceptId))[0] as biomedicalConceptId, apoc.coll.toSet(collect(datasetSpecializationId))[0] as datasetSpecializationId , collect(distinct dataElement) as vars
WITH shortName,p_dmigv, p_ds,source,datasetSpecializationId,biomedicalConceptId,vars, 
apoc.map.fromPairs([ 
                    ['packageType','sdtm'],
                    ['datasetSpecializationId',datasetSpecializationId],
                    ['domain',p_ds.uid],
                    ['shortName',shortName],
                    ['source',source],
                    ['sdtmigStartVersion',p_dmigv.version_number],
                    ['sdtmigEndVersion',null],
                    ['biomedicalConceptId',biomedicalConceptId],
                    ['variables',vars]
                    ]) as activity
return  activity

//Activity mapped to SDTM
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name='Albumin'
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R10:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R12:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R14:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrpp) 
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
OPTIONAL MATCH(p_ct2cd)<-[R23:HAS_TERM]-(clr:CTCodelistRoot)-[R24:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot)-[R27:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH(clr)-[R25:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[R26:LATEST]-(p_cl_sponsor)
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[R28:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[R29:HAS_TERM]-(cl_root)-[R30:HAS_ATTRIBUTES_ROOT]->(clattr2)-[R31:LATEST]->(unit_cld)
OPTIONAL MATCH(p_aitmc1)-[R32:HAS_ROLE]->(p_role_r:CTTermRoot), (p_role_r)-[R33:HAS_NAME_ROOT]->(ctnr_role)-[R34:LATEST]->(p_role_val), (p_role_r)-[R35:HAS_ATTRIBUTES_ROOT]->(ctattr)-[R36:LATEST]->(p_role_attr_val)
OPTIONAL MATCH(p_aitmc1)-[R37:HAS_DATA_TYPE]->(p_dtype_r),  (p_dtype_r)-[R38:HAS_NAME_ROOT]->(ctnr_dtype)-[R39:LATEST]->(p_dtype_val), (p_dtype_r)-[R40:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[R41:LATEST]->(p_dtype_attr_val)
WITH distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,R1,R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43
MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:$neodash_sdtmversion}]-(:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:$neodash_sdtmversion}]-(:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset),(p_aitm1_dom:ActivityItem)-[x]->(y:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(p_ct2_sponsor_dom), (y)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  where p_ds.uid=p_ct2_cdisc_dom.code_submission_value OPTIONAL MATCH(p_aitmc1r)-[R44:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(p_varcli:VariableClassInstance)
,(p_varcli)<-[R46:IMPLEMENTS_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dci:DatasetVariableInstance)<-[R47:HAS_DATASET_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dsi:DatasetInstance)<-[R48:HAS_INSTANCE]-(p_ds:Dataset)<-[R49:HAS_DATASET]-(p_dmcat:DataModelCatalogue)-[R50:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[R51:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[R52:CONTAINS_DATA_MODEL_IG]-(p_dmig) where p_dmigv.version_number=$neodash_sdtmversion 
return distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,p_ds,p_varcl,p_varcli,p_dci,p_dsi,p_dmcat,p_dmig, p_dmigv,R1,R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43,R44,R45,R46,R47,R48,R49,R50,R51,R52



//Activity mapped to SDTM table
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name='Albumin'
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R10:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R12:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R14:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrpp) 
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
OPTIONAL MATCH (p_aitm1)-[:HAS_UNIT_DEFINITION]->(p_unitdefr:UnitDefinitionRoot)-[R22:LATEST]->(p_unitdef:UnitDefinitionValue)
OPTIONAL MATCH(p_ct2cd)<-[R23:HAS_TERM]-(clr:CTCodelistRoot)-[R24:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot)-[R27:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH(clr)-[R25:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[R26:LATEST]-(p_cl_sponsor)
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[R28:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[R29:HAS_TERM]-(cl_root)-[R30:HAS_ATTRIBUTES_ROOT]->(clattr2)-[R31:LATEST]->(unit_cld)
OPTIONAL MATCH(p_aitmc1)-[R32:HAS_ROLE]->(p_role_r:CTTermRoot), (p_role_r)-[R33:HAS_NAME_ROOT]->(ctnr_role)-[R34:LATEST]->(p_role_val), (p_role_r)-[R35:HAS_ATTRIBUTES_ROOT]->(ctattr)-[R36:LATEST]->(p_role_attr_val)
OPTIONAL MATCH(p_aitmc1)-[R37:HAS_DATA_TYPE]->(p_dtype_r),  (p_dtype_r)-[R38:HAS_NAME_ROOT]->(ctnr_dtype)-[R39:LATEST]->(p_dtype_val), (p_dtype_r)-[R40:HAS_ATTRIBUTES_ROOT]->(ctattr_dtype)-[R41:LATEST]->(p_dtype_attr_val)
WITH distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,R1,R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43
MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:$neodash_sdtmversion}]-(:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:$neodash_sdtmversion}]-(:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset) 
MATCH(p_aitm1_dom:ActivityItem)-[x]->(y:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(p_ct2_sponsor_dom), (y)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  where p_ds.uid=p_ct2_cdisc_dom.code_submission_value 
OPTIONAL MATCH(p_aitmc1r)-[R44:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(p_varcli:VariableClassInstance)
,(p_varcli)<-[R46:IMPLEMENTS_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dci:DatasetVariableInstance)<-[R47:HAS_DATASET_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dsi:DatasetInstance)<-[R48:HAS_INSTANCE]-(p_ds:Dataset)<-[R49:HAS_DATASET]-(p_dmcat:DataModelCatalogue)-[R50:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[R51:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[R52:CONTAINS_DATA_MODEL_IG]-(p_dmig) where p_dmigv.version_number=$neodash_sdtmversion
match(p_varcl)-[R53:HAS_INSTANCE]->(s_varcli:SponsorModelVariableClassInstance)<-[R54:HAS_VARIABLE_CLASS]-(:SponsorModelDatasetClassInstance)<-[R55:HAS_INSTANCE]-(ds_class:DatasetClass)MATCH(p_aitm1_dom:ActivityItem)-[x]->(y:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(p_ct2_sponsor_dom), (y)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(p_ct2_cdisc_dom)  where p_ds.uid=p_ct2_cdisc_dom.code_submission_value 
OPTIONAL MATCH(p_aitmc1r)-[R44:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(p_varcli:VariableClassInstance)
,(p_varcli)<-[R46:IMPLEMENTS_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dci:DatasetVariableInstance)<-[R47:HAS_DATASET_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dsi:DatasetInstance)<-[R48:HAS_INSTANCE]-(p_ds:Dataset)<-[R49:HAS_DATASET]-(p_dmcat:DataModelCatalogue)-[R50:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dci)-[:HAS_INSTANCE]->(dsv:DatasetVariable),(p_dsi)<-[R51:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[R52:CONTAINS_DATA_MODEL_IG]-(p_dmig) where p_dmigv.version_number=$neodash_sdtmversion
optional match(p_dmigv)<-[:EXTENDS_VERSION]-(s_modl_val:SponsorModelValue)-[:HAS_DATASET]->(s_ds:SponsorModelDatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset)-[:HAS_INSTANCE]->(p_dsi)
Optional match(s_ds)-[:HAS_DATASET_VARIABLE]->(s_sdv:SponsorModelDatasetVariableInstance)<-[:HAS_INSTANCE]-(dsv)




