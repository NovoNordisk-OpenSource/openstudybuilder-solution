// Activity Instance Export
// Parameters needed:
//   $neodash_activity_instance_value_name - list of activity instance names (set via :param in Neo4j Browser)
//   $input - text filter for activity instance lookup

// --- Query 1: Select Activity Instances ---
MATCH (n:`ActivityInstanceValue`)-[:LATEST_FINAL]->()
WHERE toLower(toString(n.`name`)) CONTAINS toLower($input)
RETURN DISTINCT n.`name` as value, n.`name` as display
ORDER BY size(toString(value)) ASC LIMIT 20;

:param neodash_activity_instance_value_name => ["Albumin Urine"];
// --- Query 2: Activity items ---
MATCH (n1:ActivityInstanceValue)<-[:LATEST_FINAL]-()
WHERE n1.name IN $neodash_activity_instance_value_name
MATCH (n1)-[r1:CONTAINS_ACTIVITY_ITEM]-(ai:ActivityItem)

MATCH
  (ai)-[r2:HAS_ACTIVITY_ITEM]-
  (i1:ActivityItemClassRoot)-[r3:LATEST_FINAL]-
  (k1:ActivityItemClassValue)
MATCH (n1)-[r4:LATEST_FINAL]-(i2:ActivityInstanceRoot)
MATCH
  (i2)-[r5:HAS_GROUPING_ROOT]->
  (aigr:ActivityInstanceGroupingRoot)-[r30:LATEST]->
  (aigv:ActivityInstanceGroupingValue)-[r6:HAS_ACTIVITY]-
  (n10:ActivityGrouping)<-[r7:HAS_GROUPING]-
  (n11:ActivityValue)

MATCH
  (n1)-[r8:ACTIVITY_INSTANCE_CLASS]-
  (i5:ActivityInstanceClassRoot)-[r9:LATEST_FINAL]-
  (k3:ActivityInstanceClassValue)
OPTIONAL MATCH
  (ai)-[r10:HAS_CT_TERM]->(context:CTTermContext),
  (context)-[r11:HAS_SELECTED_TERM]->
  (i_term_root:CTTermRoot)<-[r12:HAS_TERM_ROOT]-
  (cl_term:CTCodelistTerm),
  (context)-[r13:HAS_SELECTED_CODELIST]->
  (cl_root:CTCodelistRoot)-[r14:HAS_TERM]->
  (cl_term),
  (cl_root)-[r22:HAS_ATTRIBUTES_ROOT]-
  (i_cl_attr_root:CTCodelistAttributesRoot)-[r88:LATEST_FINAL]-
  (cl_attr:CTCodelistAttributesValue)

OPTIONAL MATCH
  (ai)-[r21:HAS_UNIT_DEFINITION]->
  (udr:UnitDefinitionRoot)-[r22:LATEST_FINAL]->
  (udv:UnitDefinitionValue)

WITH
  n1.name AS ACTIVITY_INSTANCE_NAME,
  k3.name AS ACTIVITY_ITEM_CLASS_NAME,
  k1.name AS ACTIVITY_ITEM_TYPE,
  cl_attr.submission_value AS codelist,
  cl_term.submission_value AS term,
  "" AS IS_ADAM_PARAM_SPECIFIC
WITH
  ACTIVITY_INSTANCE_NAME,
  ACTIVITY_ITEM_CLASS_NAME,
  ACTIVITY_ITEM_TYPE,
  codelist,
  apoc.text.join(collect(DISTINCT term), '|') AS terms,
  IS_ADAM_PARAM_SPECIFIC
RETURN
  ACTIVITY_INSTANCE_NAME,
  ACTIVITY_ITEM_CLASS_NAME,
  ACTIVITY_ITEM_TYPE,
  CASE codelist
    WHEN codelist THEN apoc.text.join([codelist, terms], ':')
    ELSE ""
  END AS ACTIVITY_ITEM_VALUE,
  IS_ADAM_PARAM_SPECIFIC
ORDER BY ACTIVITY_INSTANCE_NAME, ACTIVITY_ITEM_TYPE;