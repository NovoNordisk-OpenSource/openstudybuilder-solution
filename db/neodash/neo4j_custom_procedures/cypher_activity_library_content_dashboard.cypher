/*******************************************************************************
 * UPDATED QUERIES - Activity Library Content Dashboard
 * 
 * Report: Activity Library Dashboard
 * Version: 2.4
 * Source: neodash/neodash_reports/activity_library_content_dashboard.json
 * 
 * This file contains UPDATED versions of queries affected by schema changes.
 * Only queries using the old ActivityValidGroup node have been updated.
 * All queries are ready to copy-paste into Neo4j Browser.
 * 
 * Date: January 20, 2026
 ******************************************************************************/


/*==============================================================================
 * PAGE: Activity Lib (Search Top-Down)
 * TITLE: Number of Activities (Instances per Activity, when Subgroup is Selected)
 * 
 * FULL QUERY with apoc.case - Updated DEFAULT FALLBACK branch
 *============================================================================*/

// only instance class selected
CALL apoc.case([not $neodash_activityinstanceclassvalue_name='' and $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R3:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue)
MATCH (g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-()
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue)
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return aic.name as Category,
count(distinct act) as `Number of Activities` order by Category' ,

// instance class and subclass selected
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R3:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue)
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-()
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) where aic.name in [$b]
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return agrp.name as Category,
count(distinct act) as `Number of Activities` order by Category',

// instance class, subclass and group selected
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R3:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue) where agrp.name in [$c]
MATCH (g)-[:HAS_SELECTED_SUBGROUP]-(asgrp:ActivitySubGroupValue)
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-()
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) where aic.name in [$b]
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return asgrp.name as Category,
count(distinct act) as `Number of Activities` order by Category',

// all fields selected
not $neodash_activityinstanceclassvalue_name='' and not $neodash_activityinstanceclassvalue_name_subtype='' and not $neodash_activitygroupvalue_name='' and not $neodash_activitysubgroupvalue_name='', 
'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:HAS_SELECTED_SUBGROUP]->(asgrp:ActivitySubGroupValue),
(g)-[R4:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue) where agrp.name in [$c] and asgrp.name in[$d]
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-()
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) where aic.name in [$b]
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) where aicp.name in [$a]
return act.name as Category,
count(distinct ai) as `Number of Activities` order by Category'],

'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:HAS_SELECTED_SUBGROUP]->(asgrp:ActivitySubGroupValue),
(g)-[R4:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue) 
MATCH(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-()
MATCH (ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue) 
MATCH (aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue) 
return aicp.name as Category,
count(distinct act) as `Number of Activities` order by Category',
{a:$neodash_activityinstanceclassvalue_name,
b:$neodash_activityinstanceclassvalue_name_subtype,
c:$neodash_activitygroupvalue_name, 
d:$neodash_activitysubgroupvalue_name}) YIELD value 
return value.Category as Category,
value.`Number of Activities` as`Number of Activities/Instances` order by Category;


/*==============================================================================
 * PAGE: Activity Lib (Search Top-Down)
 * TITLE: List of Activities
 * 
 * FULL QUERY with apoc.case - Updated branches 2, 3, and DEFAULT FALLBACK
 *============================================================================*/

CALL apoc.case([not $neodash_activityinstanceclassvalue_name='' 
               and $neodash_activityinstanceclassvalue_name_subtype='' 
               and $neodash_activitygroupvalue_name='' 
               and $neodash_activitysubgroupvalue_name='', 

'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:HAS_SELECTED_SUBGROUP]->(asgrp:ActivitySubGroupValue),
(g)-[R4:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue),
(g)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-(),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] 

return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity', 

not $neodash_activityinstanceclassvalue_name='' 
and not $neodash_activityinstanceclassvalue_name_subtype='' 
and $neodash_activitygroupvalue_name='' 
and $neodash_activitysubgroupvalue_name='', 

'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:HAS_SELECTED_SUBGROUP]->(asgrp:ActivitySubGroupValue),
(g)-[R4:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-(),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and aic.name in [$b] 

return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity', 

not $neodash_activityinstanceclassvalue_name='' 
and not $neodash_activityinstanceclassvalue_name_subtype='' 
and not $neodash_activitygroupvalue_name='' 
and $neodash_activitysubgroupvalue_name='', 

'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:HAS_SELECTED_SUBGROUP]->(asgrp:ActivitySubGroupValue),
(g)-[R4:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-(),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and aic.name in [$b] and agrp.name in [$c] 

return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity', 

not $neodash_activityinstanceclassvalue_name='' 
and not $neodash_activityinstanceclassvalue_name_subtype='' 
and not $neodash_activitygroupvalue_name='' 
and not $neodash_activitysubgroupvalue_name='',

'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:HAS_SELECTED_SUBGROUP]->(asgrp:ActivitySubGroupValue),
(g)-[R4:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-(),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue)
where aicp.name in [$a] and aic.name in [$b] and agrp.name in [$c] and asgrp.name in [$d] 

return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity'],

'MATCH(act:ActivityValue)-[R1:HAS_GROUPING]->(g:ActivityGrouping)-[R2:HAS_SELECTED_SUBGROUP]->(asgrp:ActivitySubGroupValue),
(g)-[R4:HAS_SELECTED_GROUP]->(agrp:ActivityGroupValue),
(g:ActivityGrouping)<-[R5:HAS_ACTIVITY]-(ai:ActivityInstanceValue)<-[:LATEST]-(),
(ai)-[R42:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)-[R43:LATEST]->(aic:ActivityInstanceClassValue),
(aitm1)<-[R8:HAS_ACTIVITY_ITEM]-(aitmc1r:ActivityItemClassRoot)-[R9:LATEST]->(aitmc1:ActivityItemClassValue),
(aicr)-[R10:PARENT_CLASS]->(aicrp:ActivityInstanceClassRoot)-[R11:LATEST]->(aicp:ActivityInstanceClassValue),
(aicrp)-[R12:PARENT_CLASS]->(aicrpp:ActivityInstanceClassRoot)-[R13:LATEST]->(aicpp:ActivityInstanceClassValue) 
return distinct aicp.name as ActivityType, aic.name as ActivitySubType, agrp.name as ActivityGroup, asgrp.name as ActivitySubGroup, act.name as Activity',{
a:$neodash_activityinstanceclassvalue_name,    
b:$neodash_activityinstanceclassvalue_name_subtype,
c:$neodash_activitygroupvalue_name, 
d:$neodash_activitysubgroupvalue_name}) YIELD value return value.ActivityType as `Activity Type`,value.ActivitySubType as `Activity Subtype`, value.ActivityGroup as `Activity Group` ,value.ActivitySubGroup as `Activity Subgroup` , value.Activity as Activity order by Activity;


/*******************************************************************************
 * END OF FILE
 * 
 * SUMMARY:
 * --------
 * - 2 queries updated for new schema (removing ActivityValidGroup node)
 * - All other queries in the dashboard already use the new schema
 * - Ready to copy-paste into Neo4j Browser for testing
 ******************************************************************************/
