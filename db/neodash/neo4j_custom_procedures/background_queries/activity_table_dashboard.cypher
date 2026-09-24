//selectors for List of activities
MATCH (p_aicr:ActivityInstanceClassRoot)-[:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[:LATEST]->(n:ActivityInstanceClassValue) where not (:ActivityInstanceClassRoot)-[:PARENT_CLASS]->(p_aicr:ActivityInstanceClassRoot) with n where toLower(toString(n.`name`)) CONTAINS toLower($input) 
RETURN DISTINCT n.`name` as value,  n.`name` as display ORDER BY size(toString(value)) ASC LIMIT 20


MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue),(g)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),(sg)-[:IN_GROUP]->(p_agrp:ActivityGroupValue)
MATCH (p_ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)-[:LATEST]->(p_aicp:ActivityInstanceClassValue) where (:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->(p_aicr:ActivityInstanceClassRoot)
OPTIONAL MATCH (p_aicr:ActivityInstanceClassRoot)-[:PARENT_CLASS]->(p_aicrpp:ActivityInstanceClassRoot)-[:LATEST]->(p_aicpp:ActivityInstanceClassValue) where not (:ActivityInstanceClassRoot)-[:PARENT_CLASS]->(p_aicpp:ActivityInstanceClassRoot) and p_aicpp.name in [$a] 
with p_aicpp.name as ActivityType where p_aicpp is not null
return distinct p_aicpp.name as ActivityType

///Histogram
CALL apoc.case([not $neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue)
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue)
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return aic.name as Category,
count(distinct act) as `Number of Activities` order by Category' , 
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue)
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) where aic.name in [$b]
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return agrp.name as Category,
count(distinct act) as `Number of Activities` order by Category', 
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue) where agrp.name in [$c]
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) where aic.name in [$b]
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return asgrp.name as Category,
count(distinct act) as `Number of Activities Instances` order by Category',
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue) where agrp.name in [$c] and asgrp.name in[$d]
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) where aic.name in [$b]
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return act.name as Category,
count(distinct ai) as `Number of Activities` order by Category'],
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue) 
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) 
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) 
return aicp.name as Category,
count(distinct act) as `Number of Activities` order by Category',
{a:$neodash_activityinstanceclassvalue_name,
b:$neodash_activityinstanceclassvalue_name_subtype,
c:$neodash_activitygroupvalue_name, 
d:$neodash_activitysubgroupvalue_name}) YIELD value 
return value.Category as Category,
value.`Number of Activities` as`Number of Activities/Instances` order by Category






//List of activities
CALL apoc.case([not $neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] 
return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance', 
not $neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and agrp.name in [$c] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance', 
not $neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='', 'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance', 
$neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',$neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where agrp.name in [$c] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',$neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where agrp.name in [$c] and asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
not $neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and agrp.name in [$c] and asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
$neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and  $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aic.name in [$b] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and aic.name in [$b] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
$neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aic.name in [$b] and agrp.name in [$c] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
$neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aic.name in [$b] and asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and aic.name in [$b] and agrp.name in [$c] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and aic.name in [$b] and asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',
$neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aic.name in [$b] and agrp.name in [$c] and asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance'],'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R7:LATEST]-(aitm1r:ActivityItemRoot)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue) 
where aicp.name in [$a] and aic.name in [$b] and agrp.name in [$c] and asgrp.name in [$d] return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.adam_param_code as ActivityInstance',{a:$neodash_activityinstanceclassvalue_name,    b:$neodash_activityinstanceclassvalue_name_subtype,c:$neodash_activitygroupvalue_name, d:$neodash_activitysubgroupvalue_name}) YIELD value return value.ActivityType as `Activity Type`,value.ActivitySubType as `Activity Sub-Type`, value.ActivityGroup as `Activity Group` ,value.ActivitySubGroup as `Activity SubGroup` , value.Activity as Activity, value.ActivityInstance as `Activity Instance` order by Activity, `Activity Instance`

//Activity in tabular format
CALL apoc.when($neodash_activity_instance='' and not $neodash_activity='','MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name=$a
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
WITH distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitm1r,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,
CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_ct2_cdisc),properties(p_ct2_sponsor)) END as ct2,
CASE WHEN p_role_r is not null THEN apoc.map.merge(properties(p_role_val),properties(p_role_attr_val)) END as role,
CASE WHEN p_dtype_r is not null THEN apoc.map.merge(properties(p_dtype_val),properties(p_dtype_attr_val)) END as dtype,
CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor)) END as cl
with p_agrp.name as ActivityGroup,
p_asgrp.name as ActivitySubGroup,
p_act.name as Activity,
p_ai.adam_param_code as `Activity Instance`,
p_aitmc1.name as `Activity Item Class`,
CASE WHEN ct2 is not null THEN ct2.name ELSE 
CASE WHEN unit_term is not null THEN unit_term.name END END  as terms,
CASE WHEN ct2 is not null THEN cl.name ELSE 
CASE WHEN unit_cld is not null THEN unit_cld.preferred_term END END as `Code List`,
role.name as Role,
dtype.name as `Data Type`
return ActivityGroup,
ActivitySubGroup,
Activity,
`Activity Instance`,
`Activity Item Class`,
apoc.text.join(collect(terms), ",") as Term,
`Code List`,
Role,
`Data Type`','MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) 
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) where p_ai.adam_param_code=$b
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
WITH distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitm1r,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,
CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_ct2_cdisc),properties(p_ct2_sponsor)) END as ct2,
CASE WHEN p_role_r is not null THEN apoc.map.merge(properties(p_role_val),properties(p_role_attr_val)) END as role,
CASE WHEN p_dtype_r is not null THEN apoc.map.merge(properties(p_dtype_val),properties(p_dtype_attr_val)) END as dtype,
CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_cl_cdisc),properties(p_cl_sponsor)) END as cl
with p_agrp.name as ActivityGroup,
p_asgrp.name as ActivitySubGroup,
p_act.name as Activity,
p_ai.adam_param_code as `Activity Instance`,
p_aitmc1.name as `Activity Item Class`,
CASE WHEN ct2 is not null THEN ct2.name ELSE 
CASE WHEN unit_term is not null THEN unit_term.name END END  as terms,
CASE WHEN ct2 is not null THEN cl.name ELSE 
CASE WHEN unit_cld is not null THEN unit_cld.preferred_term END END as `Code List`,
role.name as Role,
dtype.name as `Data Type`
return ActivityGroup,
ActivitySubGroup,
Activity,
`Activity Instance`,
`Activity Item Class`,
apoc.text.join(collect(terms), ",") as Term,
`Code List`,
Role,
`Data Type`',{a:$neodash_activity,b:$neodash_activity_instance}) YIELD value 
RETURN  value.ActivityGroup as ActivityGroup,
value.ActivitySubGroup as ActivitySubGroup,
value.Activity as Activity,
value.`Activity Item Class` as `Activity Item Class` ,
value.Term as Term,
value.`Code List` as `Code List`,
value.Role as Role,
value.`Data Type` as `Data Type`


//Activity as a graph-view (logical view)
CALL apoc.when($neodash_activity_instance='' and not $neodash_activity='',
'MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue) where p_act.name=$a
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
RETURN g,sg,p_agrp,p_asgrp,p_act,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,R3,R4,R5,R6,ct2,unit_ct,role,dtype,unit_cl,cl',
'MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue) where p_ai.adam_param_code=$b
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
RETURN g,sg,p_agrp,p_asgrp,p_act,ai,aic,aicp,aicpp,aitm1,aitmc1,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,R3,R4,R5,R6,ct2,unit_ct,role,dtype,unit_cl,cl',{a:$neodash_activity,b:$neodash_activity_instance}) YIELD value 
RETURN 
value.g,
value.sg,
value.p_agrp,
value.p_asgrp,
value.p_act,
value.ai,
value.aic,
value.aicp,
value.aicpp,
value.aitm1,
value.aitmc1,
value.r1,
value.r2,
value.r3,
value.r4,
value.r5,
value.r6,
value.r7,
value.r8,
value.r9,
value.r10,
value.r11,
value.r12,
value.r13,
value.r14,
value.R3,
value.R4,
value.R5,
value.R6,
value.ct2,
value.unit_ct,
value.role,
value.dtype,
value.unit_cl,
value.cl

// Activity as a graph-view (physical view)
CALL apoc.when($neodash_activity_instance='' 
               and not $neodash_activity='',
'MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) where p_act.name=$a
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
return distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitm1r,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,R1,R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43',
'MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue)
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem)  where p_ai.adam_param_code=$b
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
return distinct g,sg,p_agrp,p_asgrp,p_act,p_ai,p_aicr,p_aic,p_aitm1,p_aitm1r,p_aitmc1r,p_aitmc1,p_aicrp,p_aicp,p_aicrpp,p_aicpp,p_ct2cd,ct2cdr,p_ct2_sponsor,ct2att,p_ct2_cdisc,p_unitdefr,p_unitdef,clr,clatt,clattr,p_cl_sponsor,p_cl_cdisc,unit_term,cl_root,clattr2,unit_cld,p_role_r,ctattr,ctnr_role, p_role_val, p_role_attr_val,p_dtype_r,p_dtype_val, ctnr_dtype,p_dtype_attr_val,ctattr_dtype,R1,R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41,R42,R43',{a:$neodash_activity,b:$neodash_activity_instance}) YIELD value 
return
value.g,
value.sg,
value.p_agrp,
value.p_asgrp,
value.p_act,
value.p_ai,
value.p_aicr,
value.p_aic,
value.p_aitm1,
value.p_aitm1r,
value.p_aitmc1r,
value.p_aitmc1,
value.p_aicrp,
value.p_aicp,
value.p_aicrpp,
value.p_aicpp,
value.p_ct2cd,
value.ct2cdr,
value.p_ct2_sponsor,
value.ct2att,
value.p_ct2_cdisc,
value.p_unitdefr,
value.p_unitdef,
value.clr,
value.clatt,
value.clattr,
value.p_cl_sponsor,
value.p_cl_cdisc,
value.unit_term,
value.cl_root,
value.clattr2,
value.unit_cld,
value.p_role_r,
value.ctattr,
value.ctnr_role,
value.p_role_val,
value.p_role_attr_val,
value.p_dtype_r,
value.p_dtype_val,
value.ctnr_dtype,
value.p_dtype_attr_val,
value.ctattr_dtype,
value.R1,
value.R2,
value.R3,
value.R4,
value.R5,
value.R6,
value.R7,
value.R8,
value.R9,
value.R10,
value.R11,
value.R12,
value.R13,
value.R14,
value.R15,
value.R16,
value.R17,
value.R18,
value.R19,
value.R20,
value.R21,
value.R22,
value.R23,
value.R24,
value.R25,
value.R26,
value.R27,
value.R28,
value.R29,
value.R30,
value.R31,
value.R32,
value.R33,
value.R34,
value.R35,
value.R36,
value.R37,
value.R38,
value.R39,
value.R40,
value.R41,
value.R42,
value.R43

//Activity mapped to SDTM

MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) 
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) where p_ai.adam_param_code=$neodash_activity_instance
OPTIONAL MATCH(p_aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(p_aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(p_aitmc1:ActivityItemClassValue)
MATCH (p_ai:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->(p_aitm1_dom:ActivityItem)<-[:LATEST]-(:ActivityItemRoot)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:MAPS_VARIABLE_CLASS]->(:VariableClass{uid:'DOMAIN'})-[:HAS_INSTANCE]->(:VariableClassInstance)<-[:IMPLEMENTS_VARIABLE{version_number:$neodash_sdtmversion}]-(:DatasetVariableInstance)<-[:HAS_DATASET_VARIABLE{version_number:$neodash_sdtmversion}]-(:DatasetInstance)<-[:HAS_INSTANCE]-(p_ds:Dataset) where p_ds.uid=p_aitm1_dom.name
OPTIONAL MATCH(p_aitmc1r)-[R43:MAPS_VARIABLE_CLASS]->(p_varcl:VariableClass)-[R45:HAS_INSTANCE]->(p_varcli:VariableClassInstance)
,(p_varcli)<-[R46:IMPLEMENTS_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dci:DatasetVariableInstance)<-[R47:HAS_DATASET_VARIABLE{version_number:$neodash_sdtmversion}]-(p_dsi:DatasetInstance)<-[R48:HAS_INSTANCE]-(p_ds:Dataset)<-[R49:HAS_DATASET]-(p_dmcat:DataModelCatalogue)-[R50:CONTAINS_VERSION]->(p_dmig:DataModelVersion),(p_dsi)<-[R51:HAS_DATASET]-(p_dmigv:DataModelIGValue)<-[R52:CONTAINS_DATA_MODEL_IG]-(p_dmig) where p_dmigv.version_number=$neodash_sdtmversion 
return distinct 
p_act.name as Activity,
p_ai.name as `Activity Instance`,
p_aitm1.name as `Activity Item`,
p_aitmc1.name as `Activity Item Class`,
p_varcl.uid as `Variable Class`,
p_dci.label as `SDTMIG Variable`,
p_dsi.label as `SDTMIG Dataset`


//Listing Activity Instance to choose for COSMOS display
CALL apoc.when($neodash_limit_list='','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue) 
return agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.name as `Instance Name`,ai.adam_param_code as ActivityInstance','MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue) where asgrp.name in [$a] 
return agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity, ai.name as `Instance Name`, ai.adam_param_code as ActivityInstance ', {a:$neodash_limit_list}) YIELD value
return value.ActivityGroup as `Activity Group`,
value.ActivitySubGroup as `Activity Sub-group`,
value.Activity as Activity,
value.`Instance Name` as `Instance Name`,
value.ActivityInstance as `Activity Instance`

//yaml cosmos view
MATCH(p_act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:IN_SUBGROUP]->(sg:ActivityValidGroup)<-[R3:HAS_GROUP]-(p_asgrp:ActivitySubGroupValue),
(sg)-[R4:IN_GROUP]->(p_agrp:ActivityGroupValue) 
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(p_ai:ActivityInstanceValue)-[R6:CONTAINS_ACTIVITY_ITEM]->(p_aitm1:ActivityItem) where p_ai.adam_param_code=$neodash_cosmos_activity_instance
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
with distinct p_aic as aic, p_asgrp as asgrp, p_aitmc1 as aitmc1,p_ai as ai,p_unitdef as unit_ct,
CASE WHEN p_ct2cd is not null THEN apoc.map.merge(properties(p_ct2_cdisc),properties(p_ct2_sponsor)) END as ct2,
CASE WHEN p_role_r is not null THEN apoc.map.merge(properties(p_role_val),properties(p_role_attr_val)) END as role,
CASE WHEN p_dtype_r is not null THEN apoc.map.merge(properties(p_dtype_val),properties(p_dtype_attr_val)) END as dtype
WITH distinct aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,
CASE WHEN aitmc1.name='test_name_code' THEN ct2.concept_id ELSE 'C17998' END as conceptId
with distinct aic,asgrp,aitmc1,ai,unit_ct,ct2,role,dtype,conceptId,
collect(distinct(coalesce(ct2.code_submission_value,unit_ct.name))) as val_lst
WITH aic, asgrp,conceptId,dtype, aitmc1,ai, apoc.coll.flatten(collect(val_lst)) as val_list,toInteger(aitmc1.order) as var_order,apoc.text.replace(aitmc1.name," ","%20") as aitmc1_term
with aic, asgrp, conceptId,dtype, aitmc1,ai,val_list,var_order,aitmc1_term
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+aitmc1_term+"&type=match&value=term") YIELD value
WITH aic, asgrp, conceptId,dtype, aitmc1,ai,val_list,var_order, value.concepts[0].code as item_concept_id
WITH aic, asgrp, conceptId,dtype, aitmc1,ai,val_list,var_order,item_concept_id,
CASE WHEN item_concept_id='' THEN '' ELSE 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+item_concept_id END as href
WITH aic, asgrp, conceptId,dtype, aitmc1,ai,val_list,var_order,item_concept_id,href,
apoc.map.fromPairs( [
                    ['conceptId', item_concept_id],
                    ['href', href],
                    ['shortName', aitmc1.name],
                    ['dataType',dtype.name],
                    ['exampleSet',val_list]
                    ]) as varlist order by var_order
with asgrp, aic, ai, collect(distinct conceptId) as conceptId ,collect(varlist) as vars,
CASE when (apoc.any.property(aic,'name')='NumericFinding') THEN 'Quantitative' ELSE 
CASE WHEN (apoc.any.property(aic,'name')='CategoricFinding') THEN 'Ordinal' ELSE 
 null END END as aiclass
 with apoc.text.join(collect(distinct(asgrp.name)),', ') as asgrp,ai,vars,aiclass,
 CASE when size(conceptId)>1 THEN apoc.text.join(apoc.coll.removeAll(conceptId, ['C17998']),'') ELSE apoc.text.join(conceptId,'') END as conceptId
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"/parents") YIELD value
WITH asgrp, ai,vars, aiclass,conceptId, value.code as parentConceptId
CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=definitions") YIELD value 
WITH asgrp, ai,vars, aiclass,conceptId, parentConceptId, value, [def IN value.definitions where def.source="NCI"] as def 
WITH asgrp, ai,vars, aiclass,conceptId, parentConceptId, def[0]["definition"] as conceptDefinition
WITH asgrp, ai,vars, aiclass,conceptId, parentConceptId,conceptDefinition
call apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+conceptId+"?include=synonyms") YIELD value 
WITH asgrp,ai,vars,aiclass,conceptId,parentConceptId,conceptDefinition,value, [sym IN value.synonyms where sym.source="NCI"] as sym 
WITH asgrp,ai,vars,aiclass,conceptId,parentConceptId,conceptDefinition, sym[0]["name"] as conceptSynonyms
with asgrp, ai,vars, aiclass,conceptId, parentConceptId, conceptDefinition, conceptSynonyms,
 apoc.map.fromPairs([ 
                    ['packageDate','2023-04-30'],
                    ['packageType','bc'],
                    ['conceptId',conceptId],
                    ['href', 'https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&ns=ncit&code='+conceptId],
                    ['parentConceptId',parentConceptId],
                    ['category',asgrp],
                    ['shortName',ai.name],
                    ['synonym',collect(conceptSynonyms)],
                    ['resultScale',aiclass],
                    ['definition',conceptDefinition],
                    ['dataElementConcepts', vars]
                    ]) as activity
return distinct activity

//Activities used in Studies
MATCH(act:ActivityValue)<-[r1:HAS_SELECTED_ACTIVITY]-(sa:StudyActivity)<-[r2:HAS_STUDY_ACTIVITY]-(s:StudyValue),
(sa)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(vis:StudyVisit)
where act.name in $neodash_study_activity
return act.name as Activity, CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as TrialId, s.study_acronym as `Study Acronym`, vis.short_visit_label as Visit order by Activity, `Study Acronym`, vis.visit_number

//New-Activities used in Studies

call apoc.case([$neodash_operator='OR',
"MATCH(act:ActivityValue)<-[r1:HAS_SELECTED_ACTIVITY]-(sa:StudyActivity)<-[r2:HAS_STUDY_ACTIVITY]-(s:StudyValue) where act.name in $a
with distinct s, collect(distinct act.name) as Activities
return  
CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as `Trial ID`, 
s.study_acronym as `Study Acronym`, Activities
order by `Trial ID`",
$neodash_operator='AND',
"MATCH(act:ActivityValue)<-[r1:HAS_SELECTED_ACTIVITY]-(sa:StudyActivity)<-[r2:HAS_STUDY_ACTIVITY]-(s:StudyValue)
with s, collect(distinct act.name) as all_activities
with s, $a as Activities, all_activities where apoc.coll.containsAll(all_activities,$a) 
return  
CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as `Trial ID`, 
s.study_acronym as `Study Acronym`, Activities
order by `Trial ID`"], "return null",{a:$neodash_study_activity}) YIELD value
return value.`Trial ID` as `Trial ID`,
value.`Study Acronym` as `Study Acronym`,
value.Activities as Activities
//version 2
call apoc.case([$neodash_operator='OR',
"MATCH(act:ActivityValue)<-[r1:HAS_SELECTED_ACTIVITY]-(sa:StudyActivity)<-[r2:HAS_STUDY_ACTIVITY]-(s:StudyValue) where act.name in $a
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s,collect(distinct act.name) as Activities, CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as trialid
with s, Activities,trialid 
match (sr:StudyRoot)-[r0:HAS_VERSION]->(s)
OPTIONAL MATCH (sr)-[r1:LATEST]->(s)
optional match(s)<-[r:AFTER]-(sact:StudyAction)
with distinct s,Activities,trialid,sr.uid as StudyRoot, collect(r0.status) as statuses ,collect(r0.version) as versions, type(r1) as Latest,sact.date as date order by StudyRoot, sact.date
with s,Activities,StudyRoot, s.study_acronym as acronym, trialid, split(apoc.temporal.format(date, 'iso_local_date_time'),'.')[0] as Date, case when 'LOCKED' in statuses then 'LOCKED' else 'DRAFT' END as Status,
apoc.text.join(apoc.coll.toSet(versions),'') as Version,Latest 
return StudyRoot, trialid, acronym, Date, Version, Latest,Status, Activities, id(s) as sid
order by trialid",
$neodash_operator='AND',
"MATCH(act:ActivityValue)<-[r1:HAS_SELECTED_ACTIVITY]-(sa:StudyActivity)<-[r2:HAS_STUDY_ACTIVITY]-(s:StudyValue)
with s, collect(distinct act.name) as all_activities
with s, $a as Activities, all_activities where apoc.coll.containsAll(all_activities,$a) 
match(sr:StudyRoot)-[r0:HAS_VERSION]->(s:StudyValue)
with r0, s, Activities, CASE WHEN s.subpart_id is not null THEN s.study_id_prefix+'-'+s.study_number+'-'+s.subpart_id ELSE s.study_id_prefix+'-'+s.study_number END as trialid
with s, Activities,trialid 
match (sr:StudyRoot)-[r0:HAS_VERSION]->(s)
OPTIONAL MATCH (sr)-[r1:LATEST]->(s)
optional match(s)<-[r:AFTER]-(sact:StudyAction)
with distinct s,Activities,trialid,sr.uid as StudyRoot, collect(r0.status) as statuses ,collect(r0.version) as versions, type(r1) as Latest,sact.date as date order by StudyRoot, sact.date
with s,Activities,StudyRoot, s.study_acronym as acronym, trialid, split(apoc.temporal.format(date, 'iso_local_date_time'),'.')[0] as Date, case when 'LOCKED' in statuses then 'LOCKED' else 'DRAFT' END as Status,
apoc.text.join(apoc.coll.toSet(versions),'') as Version,Latest 
return StudyRoot, trialid, acronym, Date, Version, Latest,Status, Activities, id(s) as sid
order by trialid"], "return null",{a:$neodash_study_activity}) YIELD value
return value.StudyRoot as StudyRoot, 
value.trialid as `Trial ID`, 
value.acronym as Acronym, 
value.Date as Date, 
value.Version as Version, 
value.Latest as Latest,
value.Status as Status, 
value.Activities as Activities, 
value.sid as __sid

//SoA
match(s:StudyValue) where id(s) = toInteger($neodash_study_act_select )
optional match(s)-[:HAS_STUDY_VISIT]->(vis:StudyVisit)
optional match(vis)-[:HAS_VISIT_NAME]->(vis_name_root)-[:HAS_VERSION]->(vis_name:VisitNameValue)
optional match(vis)-[:STUDY_VISIT_HAS_SCHEDULE]->(schedule:StudyActivitySchedule)
optional match (s)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(schedule),
(schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(act:StudyActivity),
(act)-[:HAS_SELECTED_ACTIVITY]->(act_val:ActivityValue),(act)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(ai_s:StudyActivityInstance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]-(ai:ActivityInstanceValue),
(ai)-[r1]->(g)<-[r2]-(act_val)
with distinct schedule,vis.visit_number as `Visit ID`,vis.short_visit_label as `Visit Short Label`, act_val.name as Activity
where Activity is not null
return Activity, `Visit ID`, `Visit Short Label` order by schedule.uid



