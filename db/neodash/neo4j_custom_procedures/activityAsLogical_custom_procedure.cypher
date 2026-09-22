CALL apoc.custom.declareProcedure(
  'activityAsLogical(name::STRING) :: (row::MAP)','MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
where p_act.name=$name
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
MATCH (p_ai:ActivityInstanceValue)-[R7:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItemValue)
OPTIONAL MATCH(p_aitm1)<-[R8:LATEST]-(p_aitm1r:ActivityItemRoot)<-[R9:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R10:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R11:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R12:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R13:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R14:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R17:HAS_ITEM_CLASS]-(p_aicrpp) 
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,r1,r2,r3,p_aitm1,p_aitmc1,p_aicp,p_aicpp,R3,R4,R5,R6,R15,R16,R17,
apoc.create.vNode(["ActivityItem"],properties(p_aitm1)) as aitm1,
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
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
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
OPTIONAL MATCH(p_ct2cd)<-[R22:HAS_TERM]-(clr:CTCodelistRoot)-[R23:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot),(clr)-[R24:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[:LATEST]-(p_cl_sponsor),(clatt)-[:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[:HAS_TERM]-(cl_root)-[:HAS_ATTRIBUTES_ROOT]->(clattr2)-[:LATEST]->(unit_cld)
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,R3,R4,R5,R6,p_ct2cd,p_unitdefr,ct2,unit_ct,role,dtype,p_cl_cdisc,p_cl_sponsor,
CASE WHEN p_ct2cd is not null THEN apoc.create.vNode(["CTCodeList"],apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor))) END as cl,
CASE WHEN p_unitdefr is not null THEN
apoc.create.vNode(["CTCodeList"],properties(unit_cld)) END as unit_cl
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,R3,R4,R5,R6,p_ct2cd,p_unitdefr,ct2,unit_ct,role,dtype,cl,unit_cl,
CASE WHEN p_ct2cd is not null THEN
apoc.create.vRelationship(cl,"HAS",{type:"logical"},ct2) END as r13,
CASE WHEN p_unitdefr is not null THEN
apoc.create.vRelationship(unit_ct,"HAS",{type:"logical"},unit_cl) END as r14
RETURN g,sg,p_agrp,p_asgrp,p_act,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,R3,R4,R5,R6,ct2,unit_ct,role,dtype,unit_cl','read','Displays an activity in a logical manner based on name of activity.To call the procedure write: call custom.activityAsLogical("<activity.name>"), e.g. call custom.activityAsLogical("Albumin")')


CALL apoc.custom.declareProcedure(
  'activityInstanceAsLogical(name::STRING) :: (row::MAP)','MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(p_aic:ActivityInstanceClassValue)
where p_ai.adam_param_code=$name
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
MATCH (p_ai:ActivityInstanceValue)-[R7:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItemValue)
OPTIONAL MATCH(p_aitm1)<-[R8:LATEST]-(p_aitm1r:ActivityItemRoot)<-[R9:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R10:LATEST]->(p_aitmc1:ActivityItemClassValue)
OPTIONAL MATCH (p_aicr)-[R11:PARENT_CLASS]->(p_aicrp:ActivityInstanceClassRoot)-[R12:LATEST]->(p_aicp:ActivityInstanceClassValue)
OPTIONAL MATCH (p_aicrp)-[R13:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[R14:LATEST]->(p_aicpp:ActivityInstanceClassValue)
OPTIONAL MATCH(p_aitmc1r)<-[R15:HAS_ITEM_CLASS]-(p_aicr)
OPTIONAL MATCH(p_aitmc1r)<-[R16:HAS_ITEM_CLASS]-(p_aicrp)
OPTIONAL MATCH(p_aitmc1r)<-[R17:HAS_ITEM_CLASS]-(p_aicrpp) 
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,r1,r2,r3,p_aitm1,p_aitmc1,p_aicp,p_aicpp,R3,R4,R5,R6,R15,R16,R17,
apoc.create.vNode(["ActivityItem"],properties(p_aitm1)) as aitm1,
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
OPTIONAL MATCH (p_aitm1)-[R17]->(p_ct2cd:CTTermRoot)-[R18:HAS_NAME_ROOT]->(ct2cdr:CTTermNameRoot)-[R19:LATEST]->(p_ct2_sponsor), (p_ct2cd)-[R20:HAS_ATTRIBUTES_ROOT]->(ct2att:CTTermAttributesRoot)-[R21:LATEST]->(p_ct2_cdisc)
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
OPTIONAL MATCH(p_ct2cd)<-[R22:HAS_TERM]-(clr:CTCodelistRoot)-[R23:HAS_ATTRIBUTES_ROOT]->(clatt:CTCodelistAttributesRoot),(clr)-[R24:HAS_NAME_ROOT]->(clattr:CTCodelistNameRoot)-[:LATEST]-(p_cl_sponsor),(clatt)-[:LATEST]->(p_cl_cdisc:CTCodelistAttributesValue),(pc:CTPackageCodelist) where ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-(pc) and pc.uid CONTAINS "SDTM") or NOT ((p_cl_cdisc)<-[:CONTAINS_ATTRIBUTES]-())
OPTIONAL MATCH (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]-(unit_term:CTTermRoot)<-[:HAS_TERM]-(cl_root)-[:HAS_ATTRIBUTES_ROOT]->(clattr2)-[:LATEST]->(unit_cld)
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,R3,R4,R5,R6,p_ct2cd,p_unitdefr,ct2,unit_ct,role,dtype,p_cl_cdisc,p_cl_sponsor,
CASE WHEN p_ct2cd is not null THEN apoc.create.vNode(["CTCodeList"],apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor))) END as cl,
CASE WHEN p_unitdefr is not null THEN
apoc.create.vNode(["CTCodeList"],properties(unit_cld)) END as unit_cl
WITH g,sg,p_agrp,p_asgrp,p_act,p_ai,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,R3,R4,R5,R6,p_ct2cd,p_unitdefr,ct2,unit_ct,role,dtype,cl,unit_cl,
CASE WHEN p_ct2cd is not null THEN
apoc.create.vRelationship(cl,"HAS",{type:"logical"},ct2) END as r13,
CASE WHEN p_unitdefr is not null THEN
apoc.create.vRelationship(unit_ct,"HAS",{type:"logical"},unit_cl) END as r14
RETURN g,sg,p_agrp,p_asgrp,p_act,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,R3,R4,R5,R6,ct2,unit_ct,role,dtype,unit_cl','read','Displays an activity in a logical manner based on name of activity instance adam_param_code.To call the procedure write: call custom.activityInstanceAsLogical("<activityinstance.adam_param_code>"), e.g. call custom.activityAsLogical("ALB")')
