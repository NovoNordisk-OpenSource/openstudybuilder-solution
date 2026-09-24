// ============================================================
// Queries extracted from: neodash/neodash_reports/laboratory_data_specification.json
// Report title: Laboratory Data Specification
// ============================================================


// ------------------------------------------------------------
// Page: Lab Data Spec Metadata | Component: Select Study (required) [table]
// ------------------------------------------------------------
MATCH (n1)-[:LATEST]->(n2)-[:HAS_PROJECT]->(sp:StudyProjectField)<-[:HAS_FIELD]-(proj:Project)
WHERE
  // Scenario 1: No filters - show all studies
  (size($neodash_project_name) = 0 AND $neodash_study_id = '')
  OR
  // Scenario 2: Only project selected - show all studies in those projects
  (size($neodash_project_name) > 0 AND proj.name IN $neodash_project_name AND $neodash_study_id = '')
  OR
  // Scenario 3: Both project and study selected - show only that study
  (proj.name IN $neodash_project_name AND $neodash_study_id <> '' AND
   CASE
     WHEN n2.subpart_id IS NOT NULL
     THEN toString(proj.name + '-' + n2.study_number + '-' + n2.subpart_id)
     ELSE toString(proj.name + '-' + n2.study_number)
   END STARTS WITH $neodash_study_id)
  OR
  // Scenario 4: Only study selected - show only that study
  (size($neodash_project_name) = 0 AND $neodash_study_id <> '' AND
   CASE
     WHEN n2.subpart_id IS NOT NULL
     THEN toString(proj.name + '-' + n2.study_number + '-' + n2.subpart_id)
     ELSE toString(proj.name + '-' + n2.study_number)
   END STARTS WITH $neodash_study_id)
WITH n1, proj, n2,
  CASE
    WHEN n2.subpart_id IS NOT NULL THEN
      CASE
        WHEN n2.study_acronym IS NOT NULL
        THEN toString(proj.name + '-' + n2.study_number + '-' + n2.subpart_id) + ' [' + n2.study_acronym + ']'
        ELSE toString(proj.name + '-' + n2.study_number + '-' + n2.subpart_id)
      END
    WHEN (n2.study_number IS NOT NULL AND n2.study_acronym IS NOT NULL)
    THEN toString(proj.name + '-' + n2.study_number) + ' [' + n2.study_acronym + ']'
    ELSE toString(proj.name + '-' + n2.study_number)
  END AS StudyRef
RETURN DISTINCT 'Select' AS Click, StudyRef, n1.uid AS __uid
ORDER BY StudyRef


// ------------------------------------------------------------
// Page: Lab Data Spec Metadata | Component: Select lab specification version (required) [select]
// ------------------------------------------------------------
MATCH (model_root:DataModelIGRoot)-->(n:DataModelIGValue)
-[:HAS_DATASET]->(dataset_value:DatasetInstance)<--(:Dataset {uid: "LAB"})
WHERE toLower(apoc.text.join([n.`description`,' - V',n.version_number],"")) CONTAINS toLower($input)
RETURN DISTINCT apoc.text.join([n.`description`,' - V',n.version_number],"") as value, apoc.text.join([n.`description`,' - V',n.version_number],"") as display ORDER BY size(toString(value)) ASC LIMIT 5


// ------------------------------------------------------------
// Page: Lab Data Spec Metadata | Component: Search for a Project [select]
// ------------------------------------------------------------
MATCH (:`StudyValue`)-[:HAS_PROJECT]->(sp:StudyProjectField)<-[:HAS_FIELD]-(n:Project)
WHERE toLower(toString(n.`name`)) CONTAINS toLower($input)
RETURN DISTINCT n.`name` as value,  n.`name` as display ORDER BY size(toString(value)) ASC LIMIT 5


// ------------------------------------------------------------
// Page: Lab Data Spec Metadata | Component: Search for a Study [select]
// ------------------------------------------------------------
MATCH (n:`StudyValue`)-[:HAS_PROJECT]->(sp:StudyProjectField)<-[:HAS_FIELD]-(proj:Project) WHERE (size($neodash_project_name)>0 AND proj.name IN $neodash_project_name) OR size($neodash_project_name)=0
WITH n, proj
WHERE toLower(toString(proj.name+'-' + n.study_number)) CONTAINS toLower($input)
RETURN DISTINCT toString(proj.name+'-'+n.study_number) as value,  toString(proj.name +'-' + n.study_number) as display ORDER BY size(toString(value)) ASC LIMIT 100


// ------------------------------------------------------------
// Page: Visit | Component: Visits - $neodash_study_name [table]
// ------------------------------------------------------------
MATCH
  (n:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)-->
  (visit:StudyVisit)-[r2:HAS_VISIT_NAME]->(n3:VisitNameRoot)-->(n4:VisitNameValue)
WHERE
  // Show visits NOT in the exclusion list (default behavior)
  NOT toLower(visit.visit_class) IN ['non_visit', 'unscheduled_visit']
  OR
  // OR include excluded visits if explicitly specified in parameter
  (size($neodash_visit_class) > 0 AND visit.visit_class IN $neodash_visit_class)
OPTIONAL MATCH(visit)-->
  (s_act_sch:StudyActivitySchedule)<--
  (sact:StudyActivity)-->
  (:StudyActivitySubGroup)-->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (agv:ActivityGroupValue)
WHERE
  // LAB: Laboratory Assessments excluding Antibodies and PK Sampling
  (('LAB' IN $neodash_spec_type AND agv.name = "Laboratory Assessments" AND asgv.name <> "Antibodies" AND asgv.name <> "PK Sampling")
  OR
  // PK: PK/PD related groups
  ('PK' IN $neodash_spec_type AND (
    toLower(agv.name) IN ['pk sampling', 'pk parameter', 'pd sampling']
    OR (toLower(agv.name) = 'laboratory assessments' AND toLower(asgv.name) = 'pharmacodynamics')
  ))
  OR
  // AB: Antibodies only
  ('AB' IN $neodash_spec_type AND asgv.name = "Antibodies"))
AND NOT (s_act_sch)<--(:Delete)
WITH DISTINCT n4, visit, sact WHERE NOT (NOT visit.visit_class IN $neodash_visit_class AND sact.uid IS NULL)
WITH DISTINCT
  visit,
  CASE WHEN visit.visit_class IN $neodash_visit_class THEN apoc.text.capitalize(toLower(replace(visit.visit_class, '_', ' '))) ELSE n4.name END AS `Visit label in protocol`,
  " " AS `Visit label in supplier database`,
  CASE WHEN visit.visit_class IN $neodash_visit_class THEN CASE WHEN visit.visit_class = 'UNSCHEDULED_VISIT' THEN split(visit.visit_class, "_")[0] ELSE replace(toUpper(visit.visit_class),'_','-') END ELSE visit.short_visit_label END AS `Visit in data file`,
  toInteger(visit.unique_visit_number) AS visit_order,
  visit.visit_number AS visit_number
ORDER BY visit_order
RETURN DISTINCT
  `Visit label in protocol`,
  `Visit label in supplier database`,
  `Visit in data file`


// ------------------------------------------------------------
// Page: Visit | Component: Visits - $neodash_study_name [table] - OPTIMIZED ALTERNATIVE
// Addresses: dbms.memory.transaction.total.max threshold reached
// Changes vs original:
//   1. Explicit relationship type HAS_STUDY_VISIT (from data model) instead of anonymous -->
//      avoids scanning all outgoing relationship types from StudyValue
//   2. OPTIONAL MATCH + post-filter replaced with EXISTS {}
//      EXISTS short-circuits on first match, never materialising intermediate rows
//   3. All relationship types inside EXISTS are explicit for the same reason
//   4. Unused variables r2, n3, sact, visit_number dropped from outer scope
// NOTE: verify HAS_STUDY_VISIT and VisitNameRoot-[:LATEST]-> are correct in your schema
// ------------------------------------------------------------
MATCH (n:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->(s:StudyValue)
WITH s
MATCH (s)-[:HAS_STUDY_VISIT]->(visit:StudyVisit)
WHERE
  // Default: show scheduled visits only
  NOT visit.visit_class IN ['NON_VISIT', 'UNSCHEDULED_VISIT']
  OR
  // Include non-standard types only when explicitly selected
  (size($neodash_visit_class) > 0 AND visit.visit_class IN $neodash_visit_class)

// Fetch visit name (explicit typed path)
MATCH (visit)-[:HAS_VISIT_NAME]->(:VisitNameRoot)-[:LATEST]->(n4:VisitNameValue)

// Keep visit if it belongs to an explicitly included class
// OR if at least one qualifying scheduled activity exists (EXISTS short-circuits)
WHERE
  visit.visit_class IN $neodash_visit_class
  OR EXISTS {
    MATCH (visit)-[:STUDY_VISIT_HAS_SCHEDULE]->(sch:StudyActivitySchedule)
    WHERE NOT (sch)<--(:Delete)
    MATCH (sch)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(sact:StudyActivity)
    MATCH (sact)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
          (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
          (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
          (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->(agv:ActivityGroupValue)
    WHERE
      // LAB: Laboratory Assessments excluding Antibodies and PK Sampling
      ('LAB' IN $neodash_spec_type AND agv.name = "Laboratory Assessments"
        AND asgv.name <> "Antibodies" AND asgv.name <> "PK Sampling")
      OR
      // PK: PK/PD related groups
      ('PK' IN $neodash_spec_type AND (
        toLower(agv.name) IN ['pk sampling', 'pk parameters', 'pd sampling']
        OR (toLower(agv.name) = 'laboratory assessments' AND toLower(asgv.name) = 'pharmacodynamics')
      ))
      OR
      // AB: Antibodies only
      ('AB' IN $neodash_spec_type AND asgv.name = "Antibodies")
  }

WITH DISTINCT
  visit,
  n4,
  toInteger(visit.unique_visit_number) AS visit_order
ORDER BY visit_order
RETURN DISTINCT
  CASE WHEN visit.visit_class IN $neodash_visit_class
    THEN apoc.text.capitalize(toLower(replace(visit.visit_class, '_', ' ')))
    ELSE n4.name
  END AS `Visit label in protocol`,
  " " AS `Visit label in supplier database`,
  CASE WHEN visit.visit_class IN $neodash_visit_class
    THEN CASE WHEN visit.visit_class = 'UNSCHEDULED_VISIT'
              THEN split(visit.visit_class, "_")[0]
              ELSE replace(toUpper(visit.visit_class), '_', '-')
         END
    ELSE visit.short_visit_label
  END AS `Visit in data file`


// ------------------------------------------------------------
// Page: Visit | Component: Include non-scheduled visit types [select]
// ------------------------------------------------------------
MATCH (n:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->(s:StudyValue)-->(v:StudyVisit)
WHERE v.visit_class IN ['NON_VISIT','UNSCHEDULED_VISIT']
  AND toLower(toString(v.visit_class)) CONTAINS toLower($input)
WITH collect(DISTINCT v.visit_class) as classes
WITH CASE WHEN size(classes) = 0 THEN [null] ELSE classes END as final_classes
UNWIND final_classes as vc
RETURN vc as value, vc as display
ORDER BY size(toString(value)) ASC
LIMIT 5


// ------------------------------------------------------------
// Page: Visit | Component: Select Spec Type [select]
// ------------------------------------------------------------
WITH ["LAB","PK","AB"] as visit_types
UNWIND visit_types as visit_type
WITH visit_type
WHERE toLower(visit_type) CONTAINS toLower($input)
RETURN DISTINCT visit_type as value,  visit_type as display ORDER BY display DESC


// ------------------------------------------------------------
// Page: LAB Content | Component: TABLE 1 - REMOVE unwanted lab assessments [table]
// Marks rows with ✅/❌ based on $neodash_remove_activity_instances
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (:ActivityGroupValue {name: "Laboratory Assessments"})
WHERE asgv.name <> "Antibodies" AND asgv.name <> "PK Sampling"  AND asgv.name <> "Pharmacodynamics"
WITH DISTINCT s, s_act
MATCH (s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH (ai:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WITH DISTINCT s, act, ai
CALL {
  WITH s, act, ai
  OPTIONAL MATCH (ai)-[:CONTAINS_ACTIVITY_ITEM]->(aitm1:ActivityItem)
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(context:CTTermContext)
    WITH context
    MATCH(context)<-[:HAS_CT_DIMENSION]-(possible_units:UnitDefinitionValue)-[r1:HAS_CT_UNIT]->(x:CTTermContext)-[r2:HAS_SELECTED_TERM]->(y:CTTermRoot)<-[r3:HAS_TERM_ROOT]-(cdisc_unit:CTCodelistTerm),
  (x)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]->(cdisc_unit)
  WITH DISTINCT x, possible_units.name as pos_unit, CASE WHEN possible_units.convertible_unit THEN '*' ELSE '' END as convertible, cdisc_unit.submission_value as sub_vals
  WITH x, apoc.text.join(collect(pos_unit+convertible),';') as pos_units, sub_vals
  RETURN apoc.text.join(collect(pos_units+'['+sub_vals+']')," | ") as possible_units
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "standard_unit"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (std_unit:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(cdisc_std_unit:CTCodelistTerm)
  RETURN std_unit, cdisc_std_unit
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "specimen"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val1:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val1.submission_value) AS lbspec
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm2:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "method"})
  WITH DISTINCT aitm2
  OPTIONAL MATCH
    (aitm2)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val2:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val2.submission_value) AS lbmethod
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm3:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "original_result"})
  WITH DISTINCT aitm3
  OPTIONAL MATCH
    (aitm3)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val3:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val3.submission_value) AS lbstresc
}
WITH
  act,
  ai,
  CASE
    WHEN size(lbmethod) > 0 THEN apoc.text.join(lbmethod,";")
    ELSE ' '
  END AS lbmethod,
  CASE
    WHEN size(lbspec) > 0 THEN apoc.text.join(lbspec,";")
    ELSE ' '
  END AS lbspec,
  CASE
    WHEN possible_units='' THEN ' '
    ELSE possible_units
  END AS possible_units,
  CASE
    WHEN size(lbstresc) > 0 THEN apoc.text.join(lbstresc,";")
    ELSE ' '
  END AS lbstresc,
  CASE WHEN std_unit.name IS NULL THEN ' ' ELSE std_unit.name END AS `Standard unit`
RETURN DISTINCT
  CASE WHEN ai.topic_code IN $neodash_remove_activity_instances THEN '❌' ELSE '✅' END AS `In/Excluded`,
  act.name AS `Assessment description based on protocol`,
  ' ' AS `Supplier Assessment`,
  ' ' AS `Supplier Unit`,
  ' ' AS `Supplier Method Name`,
  ' ' AS UNITCOLL,
  lbspec AS LBSPEC,
  ai.topic_code AS TOPICCD,
  lbstresc AS `Valid LBSTRESC values for categorical results`,
  lbmethod AS LBMETHOD,
  ' ' AS LBANMETH,
  `Standard unit`,
  possible_units AS `Units in units dimension[CDISC Submission Value]`


// ------------------------------------------------------------
// Page: LAB Content | Component: TABLE 2 - Final list of assessments to export [table]
// Filters out assessments in $neodash_remove_activity_instances
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (:ActivityGroupValue {name: "Laboratory Assessments"})
WHERE asgv.name <> "Antibodies" AND asgv.name <> "PK Sampling"  AND asgv.name <> "Pharmacodynamics"
WITH DISTINCT s, s_act
MATCH (s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH (ai:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WITH DISTINCT s, act, ai WHERE size($neodash_remove_activity_instances) = 0 OR NOT ai.topic_code IN $neodash_remove_activity_instances
CALL {
  WITH s, act, ai
  OPTIONAL MATCH (ai)-[:CONTAINS_ACTIVITY_ITEM]->(aitm1:ActivityItem)
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(context:CTTermContext)
    WITH context
    MATCH(context)<-[:HAS_CT_DIMENSION]-(possible_units:UnitDefinitionValue)-[r1:HAS_CT_UNIT]->(x:CTTermContext)-[r2:HAS_SELECTED_TERM]->(y:CTTermRoot)<-[r3:HAS_TERM_ROOT]-(cdisc_unit:CTCodelistTerm),
  (x)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]->(cdisc_unit)
  WITH DISTINCT x, possible_units.name as pos_unit, CASE WHEN possible_units.convertible_unit THEN '*' ELSE '' END as convertible, cdisc_unit.submission_value as sub_vals
  WITH x, apoc.text.join(collect(pos_unit+convertible),';') as pos_units, sub_vals
  RETURN apoc.text.join(collect(pos_units+'['+sub_vals+']')," | ") as possible_units
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "standard_unit"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (std_unit:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(cdisc_std_unit:CTCodelistTerm)
  RETURN std_unit, cdisc_std_unit
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "specimen"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val1:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val1.submission_value) AS lbspec
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm2:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "method"})
  WITH DISTINCT aitm2
  OPTIONAL MATCH
    (aitm2)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val2:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val2.submission_value) AS lbmethod
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm3:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "original_result"})
  WITH DISTINCT aitm3
  OPTIONAL MATCH
    (aitm3)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val3:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val3.submission_value) AS lbstresc
}
WITH
  act,
  ai,
  CASE
    WHEN size(lbmethod) > 0 THEN apoc.text.join(lbmethod,";")
    ELSE ' '
  END AS lbmethod,
  CASE
    WHEN size(lbspec) > 0 THEN apoc.text.join(lbspec,";")
    ELSE ' '
  END AS lbspec,
  CASE
    WHEN possible_units='' THEN ' '
    ELSE possible_units
  END AS possible_units,
  CASE
    WHEN size(lbstresc) > 0 THEN apoc.text.join(lbstresc,";")
    ELSE ' '
  END AS lbstresc,
  CASE WHEN std_unit.name IS NULL THEN ' ' ELSE std_unit.name END AS `Standard unit`
RETURN DISTINCT
  act.name AS `Assessment description based on protocol`,
  ' ' AS `Supplier Assessment`,
  ' ' AS `Supplier Unit`,
  ' ' AS `Supplier Method Name`,
  ' ' AS UNITCOLL,
  lbspec AS LBSPEC,
  ai.topic_code AS TOPICCD,
  lbstresc AS `Valid LBSTRESC values for categorical results`,
  lbmethod AS LBMETHOD,
  ' ' AS LBANMETH,
  `Standard unit`,
  possible_units AS `Units in units dimension[CDISC Submission Value]`


// ------------------------------------------------------------
// Page: LAB Content | Component: Removed Activity Instance [table]
// Shows the list of topic codes currently selected for removal
// ------------------------------------------------------------
WITH $neodash_remove_activity_instances AS topic_codes
UNWIND topic_codes AS topic_code
RETURN topic_code AS `Assessments`


// ------------------------------------------------------------
// Page: LAB Content | Component: Select assessments to REMOVE [select]
// Populates the multi-select dropdown for LAB assessment removal
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (:ActivityGroupValue {name: "Laboratory Assessments"})
WHERE asgv.name <> "Antibodies" AND asgv.name <> "PK Sampling"  AND asgv.name <> "Pharmacodynamics"
WITH DISTINCT s, s_act
MATCH (s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH (n:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WHERE toLower(toString(n.topic_code)) CONTAINS toLower($input)
RETURN DISTINCT n.topic_code AS value, n.topic_code AS display ORDER BY size(toString(value)) ASC LIMIT 100


// ------------------------------------------------------------
// Page: PK Content | Component: TABLE 1 - REMOVE unwanted PK assessments [table]
// Marks rows with ✅/❌ based on $neodash_remove_pk_activity_instances
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (agv:ActivityGroupValue)
WITH DISTINCT s, s_act, agv, asgv WHERE (toLower(agv.name) IN ['pk sampling','pk parameters']) OR (toLower(agv.name) IN ['pd sampling']) OR (toLower(agv.name)='laboratory assessments' AND toLower(asgv.name)='pharmacodynamics')
WITH DISTINCT s, s_act
MATCH (s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH (ai:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WITH DISTINCT s, act, ai
CALL {
  WITH s, act, ai
  OPTIONAL MATCH (ai)-[:CONTAINS_ACTIVITY_ITEM]->(aitm1:ActivityItem)
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(context:CTTermContext)
    WITH context
    MATCH(context)<-[:HAS_CT_DIMENSION]-(possible_units:UnitDefinitionValue)-[r1:HAS_CT_UNIT]->(x:CTTermContext)-[r2:HAS_SELECTED_TERM]->(y:CTTermRoot)<-[r3:HAS_TERM_ROOT]-(cdisc_unit:CTCodelistTerm),
  (x)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]->(cdisc_unit)
  WITH DISTINCT x, possible_units.name as pos_unit, CASE WHEN possible_units.convertible_unit THEN '*' ELSE '' END as convertible, cdisc_unit.submission_value as sub_vals
  WITH x, apoc.text.join(collect(pos_unit+convertible),';') as pos_units, sub_vals
  RETURN apoc.text.join(collect(pos_units+'['+sub_vals+']')," | ") as possible_units
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "standard_unit"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (std_unit:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(cdisc_std_unit:CTCodelistTerm)
  RETURN std_unit, cdisc_std_unit
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "specimen"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val1:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val1.submission_value) AS lbspec
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm2:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "method"})
  WITH DISTINCT aitm2
  OPTIONAL MATCH
    (aitm2)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val2:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val2.submission_value) AS lbmethod
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm3:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "original_result"})
  WITH DISTINCT aitm3
  OPTIONAL MATCH
    (aitm3)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val3:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val3.submission_value) AS lbstresc
}
WITH
  act,
  ai,
  CASE
    WHEN size(lbmethod) > 0 THEN apoc.text.join(lbmethod,";")
    ELSE ' '
  END AS lbmethod,
  CASE
    WHEN size(lbspec) > 0 THEN apoc.text.join(lbspec,";")
    ELSE ' '
  END AS lbspec,
  CASE
    WHEN possible_units='' THEN ' '
    ELSE possible_units
  END AS possible_units,
  CASE
    WHEN size(lbstresc) > 0 THEN apoc.text.join(lbstresc,";")
    ELSE ' '
  END AS lbstresc,
  CASE WHEN std_unit.name IS NULL THEN ' ' ELSE std_unit.name END AS `Standard unit`
RETURN DISTINCT
  CASE WHEN ai.topic_code IN $neodash_remove_pk_activity_instances THEN '❌' ELSE '✅' END AS `In/Excluded`,
  act.name AS `Assessment description based on protocol`,
  ' ' AS `Supplier Assessment`,
  ' ' AS `Supplier Unit`,
  ' ' AS `Supplier Method Name`,
  ' ' AS UNITCOLL,
  lbspec AS PCSPEC,
  ai.topic_code AS TOPICCD,
  lbmethod AS PCMETHOD,
  `Standard unit`,
  possible_units AS `Units in units dimension[CDISC Submission Value]`


// ------------------------------------------------------------
// Page: PK Content | Component: TABLE 2 - Final list of assessments to export [table]
// Filters out assessments in $neodash_remove_pk_activity_instances
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (agv:ActivityGroupValue)
WITH DISTINCT s, s_act, agv, asgv WHERE (toLower(agv.name) IN ['pk sampling','pk parameters']) OR (toLower(agv.name) IN ['pd sampling']) OR (toLower(agv.name)='laboratory assessments' AND toLower(asgv.name)='pharmacodynamics')
WITH DISTINCT s, s_act
MATCH (s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH (ai:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WITH DISTINCT s, act, ai WHERE size($neodash_remove_pk_activity_instances) = 0 OR NOT ai.topic_code IN $neodash_remove_pk_activity_instances
CALL {
  WITH s, act, ai
  OPTIONAL MATCH (ai)-[:CONTAINS_ACTIVITY_ITEM]->(aitm1:ActivityItem)
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(context:CTTermContext)
    WITH context
    MATCH(context)<-[:HAS_CT_DIMENSION]-(possible_units:UnitDefinitionValue)-[r1:HAS_CT_UNIT]->(x:CTTermContext)-[r2:HAS_SELECTED_TERM]->(y:CTTermRoot)<-[r3:HAS_TERM_ROOT]-(cdisc_unit:CTCodelistTerm),
  (x)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]->(cdisc_unit)
  WITH DISTINCT x, possible_units.name as pos_unit, CASE WHEN possible_units.convertible_unit THEN '*' ELSE '' END as convertible, cdisc_unit.submission_value as sub_vals
  WITH x, apoc.text.join(collect(pos_unit+convertible),';') as pos_units, sub_vals
  RETURN apoc.text.join(collect(pos_units+'['+sub_vals+']')," | ") as possible_units
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "standard_unit"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (std_unit:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(cdisc_std_unit:CTCodelistTerm)
  RETURN std_unit, cdisc_std_unit
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "specimen"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val1:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val1.submission_value) AS lbspec
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm2:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "method"})
  WITH DISTINCT aitm2
  OPTIONAL MATCH
    (aitm2)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val2:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val2.submission_value) AS lbmethod
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm3:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "original_result"})
  WITH DISTINCT aitm3
  OPTIONAL MATCH
    (aitm3)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val3:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val3.submission_value) AS lbstresc
}
WITH
  act,
  ai,
  CASE
    WHEN size(lbmethod) > 0 THEN apoc.text.join(lbmethod,";")
    ELSE ' '
  END AS lbmethod,
  CASE
    WHEN size(lbspec) > 0 THEN apoc.text.join(lbspec,";")
    ELSE ' '
  END AS lbspec,
  CASE
    WHEN possible_units='' THEN ' '
    ELSE possible_units
  END AS possible_units,
  CASE
    WHEN size(lbstresc) > 0 THEN apoc.text.join(lbstresc,";")
    ELSE ' '
  END AS lbstresc,
  CASE WHEN std_unit.name IS NULL THEN ' ' ELSE std_unit.name END AS `Standard unit`
RETURN DISTINCT
  act.name AS `Assessment description based on protocol`,
  ' ' AS `Supplier Assessment`,
  ' ' AS `Supplier Unit`,
  ' ' AS `Supplier Method Name`,
  ' ' AS UNITCOLL,
  lbspec AS PCSPEC,
  ai.topic_code AS TOPICCD,
  lbmethod AS PCMETHOD,
  `Standard unit`,
  possible_units AS `Units in units dimension[CDISC Submission Value]`


// ------------------------------------------------------------
// Page: PK Content | Component: Removed Activity Instance [table]
// Shows the list of topic codes currently selected for removal
// ------------------------------------------------------------
WITH $neodash_remove_pk_activity_instances AS topic_codes
UNWIND topic_codes AS topic_code
RETURN topic_code AS `Assessments`


// ------------------------------------------------------------
// Page: PK Content | Component: Select assessments to REMOVE [select]
// Populates the multi-select dropdown for PK assessment removal
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (agv:ActivityGroupValue)
WITH DISTINCT s, s_act, agv, asgv WHERE (toLower(agv.name) IN ['pk sampling','pk parameters']) OR (toLower(agv.name) IN ['pd sampling']) OR (toLower(agv.name)='laboratory assessments' AND toLower(asgv.name)='pharmacodynamics')
WITH DISTINCT s, s_act
MATCH (s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH(n:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WHERE toLower(toString(n.topic_code)) CONTAINS toLower($input)
RETURN DISTINCT n.topic_code AS value, n.topic_code AS display ORDER BY size(toString(value)) ASC LIMIT 100


// ------------------------------------------------------------
// Page: AB Content | Component: TABLE 1 - REMOVE unwanted AB assessments [table]
// Marks rows with ✅/❌ based on $neodash_remove_ab_activity_instances
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (:ActivityGroupValue)
WHERE asgv.name = "Antibodies"
WITH DISTINCT s, s_act
MATCH(s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH (ai:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WITH DISTINCT s, act, ai
CALL {
  WITH s, act, ai
  OPTIONAL MATCH (ai)-[:CONTAINS_ACTIVITY_ITEM]->(aitm1:ActivityItem)
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(context:CTTermContext)
    WITH context
    MATCH(context)<-[:HAS_CT_DIMENSION]-(possible_units:UnitDefinitionValue)-[r1:HAS_CT_UNIT]->(x:CTTermContext)-[r2:HAS_SELECTED_TERM]->(y:CTTermRoot)<-[r3:HAS_TERM_ROOT]-(cdisc_unit:CTCodelistTerm),
  (x)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]->(cdisc_unit)
  WITH DISTINCT x, possible_units.name as pos_unit, CASE WHEN possible_units.convertible_unit THEN '*' ELSE '' END as convertible, cdisc_unit.submission_value as sub_vals
  WITH x, apoc.text.join(collect(pos_unit+convertible),';') as pos_units, sub_vals
  RETURN apoc.text.join(collect(pos_units+'['+sub_vals+']')," | ") as possible_units
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "standard_unit"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (std_unit:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(cdisc_std_unit:CTCodelistTerm)
  RETURN std_unit, cdisc_std_unit
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "specimen"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val1:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val1.submission_value) AS lbspec
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm2:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "method"})
  WITH DISTINCT aitm2
  OPTIONAL MATCH
    (aitm2)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val2:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val2.submission_value) AS lbmethod
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm3:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "original_result"})
  WITH DISTINCT aitm3
  OPTIONAL MATCH
    (aitm3)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val3:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val3.submission_value) AS lbstresc
}
WITH
  act,
  ai,
  CASE
    WHEN size(lbmethod) > 0 THEN apoc.text.join(lbmethod,";")
    ELSE ' '
  END AS lbmethod,
  CASE
    WHEN size(lbspec) > 0 THEN apoc.text.join(lbspec,";")
    ELSE ' '
  END AS lbspec,
  CASE
    WHEN possible_units='' THEN ' '
    ELSE possible_units
  END AS possible_units,
  CASE
    WHEN size(lbstresc) > 0 THEN apoc.text.join(lbstresc,";")
    ELSE ' '
  END AS lbstresc,
  CASE WHEN std_unit.name IS NULL THEN ' ' ELSE std_unit.name END AS `Standard unit`
RETURN DISTINCT
  CASE WHEN ai.topic_code IN $neodash_remove_ab_activity_instances THEN '❌' ELSE '✅' END AS `In/Excluded`,
  act.name AS `Assessment description based on protocol`,
  ' ' AS `Supplier Assessment`,
  ' ' AS `Supplier Unit`,
  ' ' AS `Supplier Method Name`,
  ' ' AS UNITCOLL,
  lbspec AS SPEC,
  ai.topic_code AS TOPICCD,
  lbstresc AS `If result is categorical, specify valid ORRES values from categorical response list`,
  lbmethod AS METHOD,
  `Standard unit`,
  possible_units AS `Units in units dimension[CDISC Submission Value]`


// ------------------------------------------------------------
// Page: AB Content | Component: TABLE 2 - Final list of assessments to export [table]
// Filters out assessments in $neodash_remove_ab_activity_instances
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (:ActivityGroupValue)
WHERE asgv.name = "Antibodies"
WITH DISTINCT s, s_act
MATCH(s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
(s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH (ai:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WITH DISTINCT s, act, ai WHERE size($neodash_remove_ab_activity_instances) = 0 OR NOT ai.topic_code IN $neodash_remove_ab_activity_instances
CALL {
  WITH s, act, ai
  OPTIONAL MATCH (ai)-[:CONTAINS_ACTIVITY_ITEM]->(aitm1:ActivityItem)
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (p_unitdef:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(context:CTTermContext)
    WITH context
    MATCH(context)<-[:HAS_CT_DIMENSION]-(possible_units:UnitDefinitionValue)-[r1:HAS_CT_UNIT]->(x:CTTermContext)-[r2:HAS_SELECTED_TERM]->(y:CTTermRoot)<-[r3:HAS_TERM_ROOT]-(cdisc_unit:CTCodelistTerm),
  (x)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]->(cdisc_unit)
  WITH DISTINCT x, possible_units.name as pos_unit, CASE WHEN possible_units.convertible_unit THEN '*' ELSE '' END as convertible, cdisc_unit.submission_value as sub_vals
  WITH x, apoc.text.join(collect(pos_unit+convertible),';') as pos_units, sub_vals
  RETURN apoc.text.join(collect(pos_units+'['+sub_vals+']')," | ") as possible_units
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "standard_unit"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_UNIT_DEFINITION]->
    (:UnitDefinitionRoot)-[:LATEST]->
    (std_unit:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(cdisc_std_unit:CTCodelistTerm)
  RETURN std_unit, cdisc_std_unit
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm1:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "specimen"})
  WITH DISTINCT aitm1
  OPTIONAL MATCH
    (aitm1)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val1:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val1.submission_value) AS lbspec
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm2:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "method"})
  WITH DISTINCT aitm2
  OPTIONAL MATCH
    (aitm2)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val2:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val2.submission_value) AS lbmethod
}
CALL {
  WITH s, act, ai
  OPTIONAL MATCH
    (ai)-[:CONTAINS_ACTIVITY_ITEM]->
    (aitm3:ActivityItem)<--
    (:ActivityItemClassRoot)-[:LATEST]->
    (:ActivityItemClassValue {name: "original_result"})
  WITH DISTINCT aitm3
  OPTIONAL MATCH
    (aitm3)-[:HAS_CT_TERM]->
    (:CTTermContext)-[:HAS_SELECTED_TERM]->
    (:CTTermRoot)<-[:HAS_TERM_ROOT]-(subm_val3:CTCodelistTerm)
  RETURN collect(DISTINCT subm_val3.submission_value) AS lbstresc
}
WITH
  act,
  ai,
  CASE
    WHEN size(lbmethod) > 0 THEN apoc.text.join(lbmethod,";")
    ELSE ' '
  END AS lbmethod,
  CASE
    WHEN size(lbspec) > 0 THEN apoc.text.join(lbspec,";")
    ELSE ' '
  END AS lbspec,
  CASE
    WHEN possible_units='' THEN ' '
    ELSE possible_units
  END AS possible_units,
  CASE
    WHEN size(lbstresc) > 0 THEN apoc.text.join(lbstresc,";")
    ELSE ' '
  END AS lbstresc,
  CASE WHEN std_unit.name IS NULL THEN ' ' ELSE std_unit.name END AS `Standard unit`
RETURN DISTINCT
  act.name AS `Assessment description based on protocol`,
  ' ' AS `Supplier Assessment`,
  ' ' AS `Supplier Unit`,
  ' ' AS `Supplier Method Name`,
  ' ' AS UNITCOLL,
  lbspec AS SPEC,
  ai.topic_code AS TOPICCD,
  lbstresc AS `If result is categorical, specify valid ORRES values from categorical response list`,
  lbmethod AS METHOD,
  `Standard unit`,
  possible_units AS `Units in units dimension[CDISC Submission Value]`


// ------------------------------------------------------------
// Page: AB Content | Component: Removed Activity Instance [table]
// Shows the list of topic codes currently selected for removal
// ------------------------------------------------------------
WITH $neodash_remove_ab_activity_instances AS topic_codes
UNWIND topic_codes AS topic_code
RETURN topic_code AS `Assessments`


// ------------------------------------------------------------
// Page: AB Content | Component: Select assessments to REMOVE [select]
// Populates the multi-select dropdown for AB assessment removal
// ------------------------------------------------------------
MATCH
  (:StudyRoot {uid: $neodash_studyroot_uid})-[:LATEST]->
  (s:StudyValue)
WITH s
MATCH(s)-->
  (s_act:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
  (:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
  (asgv:ActivitySubGroupValue)<-[:HAS_SELECTED_SUBGROUP]-
  (:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
  (:ActivityGroupValue)
WHERE asgv.name = "Antibodies"
WITH DISTINCT s, s_act
MATCH
  (s)-[:HAS_STUDY_ACTIVITY]->(s_act)-[:HAS_SELECTED_ACTIVITY]->(act:ActivityValue),
  (s_act)
MATCH(s_act)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(s_act_sch:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)<--(s)
WHERE NOT (s_act_sch)<--(:Delete)
MATCH(n:ActivityInstanceValue)<-[:HAS_SELECTED_ACTIVITY_INSTANCE]-
  (s_ai:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-
  (s),(s_act)-->(s_ai)
WHERE toLower(toString(n.topic_code)) CONTAINS toLower($input)
RETURN DISTINCT n.topic_code AS value, n.topic_code AS display ORDER BY size(toString(value)) ASC LIMIT 100
