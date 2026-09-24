// setting params for CRF versioning
:param neodash_odmstudyeventvalue_name=>'CRF versioning collection';
:param neodash_coll_base_id=>'4:a0e8f0d0-ecd0-4ba0-91cc-7843c426d755:234837';//V1.0
:param neodash_coll_base_id=>'4:a0e8f0d0-ecd0-4ba0-91cc-7843c426d755:234929';//V2.0
:param neodash_coll_base_id=>'4:a0e8f0d0-ecd0-4ba0-91cc-7843c426d755:234932';//V3.0
:param neodash_coll_comp_id=>'4:a0e8f0d0-ecd0-4ba0-91cc-7843c426d755:234942';//V4.0
:param neodash_coll_comp_id=>'4:a0e8f0d0-ecd0-4ba0-91cc-7843c426d755:234969';//V5.0

// general query
match(coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue) where coll.name=$neodash_odmstudyeventvalue_name
//Get form and its details
optional match(coll)-[r1_1:FORM_REF]->(form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot)
optional match(form)-[r1_2:HAS_DESCRIPTION]->(form_desc:OdmDescription)
optional match(form)-[r1_3:HAS_ALIAS]->(form_alias:OdmAlias)
optional match(form)-[r1_4:HAS_VENDOR_ELEMENT]->(f_ext_elem:OdmVendorElementValue)<-[r1_5:HAS_VENDOR_ELEMENT]-(f_elem_vendor_ns:OdmVendorNamespaceValue)<-[f_elem_vendor_ns_version:HAS_VERSION]-(),(f_ext_elem)<-[f_ext_elem_version:HAS_VERSION]-()
optional match(form)-[f_value1:HAS_VENDOR_ATTRIBUTE]->(f_ext_att:OdmVendorAttributeValue)<-[r1_7:HAS_VENDOR_ATTRIBUTE]-(f_att_vendor_ns:OdmVendorNamespaceValue)<-[f_att_vendor_ns_version:HAS_VERSION]-(),(f_ext_att)<-[f_ext_att_version:HAS_VERSION]-()
optional match(form)-[f_value2:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(f_att_val:OdmVendorAttributeValue)<-[r1_8:HAS_VENDOR_ATTRIBUTE]-(f_ext_elem)
//Get the groups in the form and the group details
optional match(form)-[r1_4:ITEM_GROUP_REF]->(group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot)
optional match(group)-[r2_1:HAS_DESCRIPTION]->(group_desc:OdmDescription)
optional match(group)-[r2_2:HAS_ALIAS]->(group_alias:OdmAlias)
optional match(group)-[r2_3:HAS_SDTM_DOMAIN]->(g_context:CTTermContext)-[r2_4:HAS_SELECTED_TERM]->(g_term_root:CTTermRoot)<-[r2_5:HAS_TERM_ROOT]-(domain:CTCodelistTerm)
optional match(group)-[r2_6:HAS_VENDOR_ELEMENT]->(g_ext_elem:OdmVendorElementValue)<-[r2_7:HAS_VENDOR_ELEMENT]-(g_elem_vendor_ns:OdmVendorNamespaceValue)<-[g_elem_vendor_ns_version:HAS_VERSION]-(),(g_ext_elem)<-[g_ext_elem_version:HAS_VERSION]-()
optional match(group)-[g_value1:HAS_VENDOR_ATTRIBUTE]->(g_ext_att:OdmVendorAttributeValue)<-[r2_9:HAS_VENDOR_ATTRIBUTE]-(g_att_vendor_ns:OdmVendorNamespaceValue)<-[g_att_vendor_ns_version:HAS_VERSION]-(),(g_ext_att)<-[g_ext_att_version:HAS_VERSION]-()
optional match(group)-[g_value2:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(g_att_val:OdmVendorAttributeValue)<-[r2_10:HAS_VENDOR_ATTRIBUTE]-(g_ext_elem)
// get the items in the groups and the item details
optional match(group)-[r3_1:ITEM_REF]->(item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot)
optional match(item)-[r3_2:HAS_DESCRIPTION]->(item_desc:OdmDescription)
optional match(item)-[r3_3:HAS_ALIAS]->(item_alias:OdmAlias)
optional match(item)-[r3_4:HAS_CODELIST_TERM]->(i_context:CTTermContext)-[r3_5:HAS_SELECTED_TERM]->(i_term_root:CTTermRoot)<-[r3_6:HAS_TERM_ROOT]-(item_term:CTCodelistTerm)
optional match(item)-[r3_7:HAS_VENDOR_ELEMENT]->(i_ext_elem:OdmVendorElementValue)<-[r3_8:HAS_VENDOR_ELEMENT]-(i_elem_vendor_ns:OdmVendorNamespaceValue)<-[i_elem_vendor_ns_version:HAS_VERSION]-(),(i_ext_elem)<-[i_ext_elem_version:HAS_VERSION]-()
optional match(item)-[i_value1:HAS_VENDOR_ATTRIBUTE]->(i_ext_att:OdmVendorAttributeValue)<-[r3_10:HAS_VENDOR_ATTRIBUTE]-(i_att_vendor_ns:OdmVendorNamespaceValue)<-[i_att_vendor_ns_version:HAS_VERSION]-(),(i_ext_att)<-[i_ext_att_version:HAS_VERSION]-()
optional match(item)-[i_value2:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(i_att_val:OdmVendorAttributeValue)<-[r3_11:HAS_VENDOR_ATTRIBUTE]-(i_ext_elem)
return *

//**************************//
//Collections
//**************************//

//select base and compare
match(coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue) where coll.name=$neodash_odmstudyeventvalue_name
return coll.name as `CRF Collection`, coll_version.version as Version, 'Base' as Select, elementId(coll) as __coll_id

//Show selected for comparison
WITH [
  {id: $neodash_coll_base_id, version: $neodash_coll_base_version_num, label: 'Base'},
  {id: $neodash_coll_comp_id, version: $neodash_coll_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)
WHERE elementId(coll) = selection.id 
  AND coll_version.version = selection.version

RETURN
  selection.label as Comparison,
  coll.name as `Collection Name`,
  coll_version.version as Version
ORDER BY Comparison, Version

// Forms in the base and compare collection
WITH [
  {id: $neodash_coll_base_id, version: $neodash_coll_base_version_num, label: 'Base'},
  {id: $neodash_coll_comp_id, version: $neodash_coll_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)
WHERE elementId(coll) = selection.id 
  AND coll_version.version = selection.version
OPTIONAL MATCH
  (coll)-[r1_1:FORM_REF]->
  (form:OdmFormValue)<-[form_version:HAS_VERSION]-
  (form_root:OdmFormRoot)
OPTIONAL MATCH (form)-[r1_2:HAS_DESCRIPTION]->(form_desc:OdmDescription)
OPTIONAL MATCH (form)-[r1_3:HAS_ALIAS]->(form_alias:OdmAlias)
OPTIONAL MATCH (form)-[r1_4:HAS_VENDOR_ELEMENT]->(f_ext_elem:OdmVendorElementValue)<-[r1_5:HAS_VENDOR_ELEMENT]-(f_elem_vendor_ns:OdmVendorNamespaceValue)<-[f_elem_vendor_ns_version:HAS_VERSION]-(),(f_ext_elem)<-[f_ext_elem_version:HAS_VERSION]-()
OPTIONAL MATCH (form)-[r1_6:HAS_VENDOR_ATTRIBUTE]->(f_ext_att:OdmVendorAttributeValue)<-[r1_7:HAS_VENDOR_ATTRIBUTE]-(f_att_vendor_ns:OdmVendorNamespaceValue)<-[f_att_vendor_ns_version:HAS_VERSION]-(),(f_ext_att)<-[f_ext_att_version:HAS_VERSION]-()
WITH DISTINCT
  selection.label as collection,
  coll_version,
  form,
  CASE
    WHEN
      form_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(form_alias))
            | ["alias-" + key, properties(form_alias)[key]]
          ])
    ELSE {}
  END AS aliasMap,
  CASE
    WHEN
      form_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(form_desc))
            | ["desc-" + key, properties(form_desc)[key]]
          ])
    ELSE {}
  END AS descMap,
  CASE
  WHEN f_ext_elem IS NOT NULL AND f_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_ext_elem)) | ["elemExt-" + key, properties(f_ext_elem)[key]+'(V'+f_ext_elem_version.version+')']])
  ELSE {}
END AS f_ext_elemMap,
CASE
  WHEN f_ext_att IS NOT NULL AND f_ext_att_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_ext_att)) | ["attExt-" + key, properties(f_ext_att)[key]+'(V'+f_ext_att_version.version+')']])
  ELSE {}
END AS f_ext_attMap,
CASE
  WHEN f_elem_vendor_ns IS NOT NULL AND f_elem_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_elem_vendor_ns)) | ["elem_nsExt-" + key, properties(f_elem_vendor_ns)[key]+'(V'+f_elem_vendor_ns_version.version+')']])
  ELSE {}
END AS f_elem_vendor_nsMap,
CASE
  WHEN f_att_vendor_ns IS NOT NULL AND f_att_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_att_vendor_ns)) | ["att_nsExt-" + key, properties(f_att_vendor_ns)[key]+'(V'+f_att_vendor_ns_version.version+')']])
  ELSE {}
END AS f_att_vendor_nsMap,
  coalesce(properties(form), {}) AS formMap
WITH
  collection,
  coll_version,
  form,
 apoc.map.mergeList([formMap, descMap, aliasMap, f_att_vendor_nsMap, f_elem_vendor_nsMap, f_ext_attMap, f_ext_elemMap]) AS props_map
UNWIND keys(props_map) AS field
WITH
  form.oid AS OID,
  field,
  apoc.map.fromPairs(collect([collection, props_map[field]])) AS value_map
WITH
  OID AS `CRF OID`,
  CASE split(field, '-')[0]
  WHEN 'elem_nsExt' THEN '7ElementVendorExtNameSpace'
  WHEN 'elemExt' THEN '6ElementVendorExt'
  WHEN 'att_nsExt' THEN '5AttributeVendorExtNameSpace'
  WHEN 'attExt' THEN '4AttributeVendorExt'
  WHEN 'desc' THEN '2Description'
  WHEN 'alias' THEN '3Alias'
  ELSE '1Identification'
END AS area,
  CASE WHEN split(field, '-')[0] IN ['desc', 'alias', 'attExt','elemExt','elem_nsExt','att_nsExt'] 
     THEN split(field, '-')[1]  
     ELSE field 
END AS `CRF attribute`,  
  replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
  replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `CRF OID`, area, `CRF attribute`
WITH `CRF OID`,area, `CRF attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `CRF OID`,substring(area,1) as Area, `CRF attribute`, Base, Compare, __diff


//Bar chart
// Count of forms per version
WITH [
  {id: $neodash_coll_base_id, version: $neodash_coll_base_version_num, label: 'Base'},
  {id: $neodash_coll_comp_id, version: $neodash_coll_comp_version_num, label: 'Compare'}
] AS selections
UNWIND selections AS selection
MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)
WHERE elementId(coll) = selection.id 
  AND coll_version.version = selection.version
OPTIONAL MATCH p=(coll)-[:FORM_REF]->(form:OdmFormValue)
RETURN selection.label+'-V'+toString(coll_version.version) AS version, 
       toInteger(COUNT(DISTINCT form)) AS `Form count`,
       'FORM_COUNT' AS metric_type


// Count of groups by form per version
//Select crf - parameter select
MATCH
  (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->
  (coll:OdmStudyEventValue)
WHERE elementId(coll) IN [$neodash_coll_base_id, $neodash_coll_comp_id]
OPTIONAL MATCH (coll)-[:FORM_REF]->(form:OdmFormValue)
WHERE toLower(toString(form.`oid`)) CONTAINS toLower($input) 
RETURN DISTINCT form.`oid` as value,  form.`oid` as display ORDER BY size(toString(value)) ASC LIMIT 100

//bar chart of groups - for selected crf
WITH [
  {id: $neodash_coll_base_id, version: $neodash_coll_base_version_num, label: 'Base'},
  {id: $neodash_coll_comp_id, version: $neodash_coll_comp_version_num, label: 'Compare'}
] AS selections
UNWIND selections AS selection
MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)
WHERE elementId(coll) = selection.id 
  AND coll_version.version = selection.version
OPTIONAL MATCH (coll)-[:FORM_REF]->(form:OdmFormValue) where form.oid=$neodash_select_crf
OPTIONAL MATCH (form)-[:ITEM_GROUP_REF]->(group:OdmItemGroupValue)
RETURN selection.label+'-V'+toString(coll_version.version) AS version,
        toInteger(COUNT(DISTINCT group)) AS `Group count`,
        'GROUP_COUNT' AS metric_type


// Count of items in groups per version
//Select group in crf in collection
MATCH
  (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->
  (coll:OdmStudyEventValue)
WHERE elementId(coll) IN [$neodash_coll_base_id, $neodash_coll_comp_id]
OPTIONAL MATCH (coll)-[:FORM_REF]->(form:OdmFormValue) where form.oid=$neodash_select_crf
OPTIONAL MATCH (form)-[:ITEM_GROUP_REF]->(group:OdmItemGroupValue)
WHERE toLower(toString(group.`oid`)) CONTAINS toLower($input) 
RETURN DISTINCT group.`oid` as value,  group.`oid` as display ORDER BY size(toString(value)) ASC LIMIT 100

//bar chart for items for select group, crf and collection
WITH [
  {id: $neodash_coll_base_id, version: $neodash_coll_base_version_num, label: 'Base'},
  {id: $neodash_coll_comp_id, version: $neodash_coll_comp_version_num, label: 'Compare'}
] AS selections
UNWIND selections AS selection
MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)
WHERE elementId(coll) = selection.id 
  AND coll_version.version = selection.version
OPTIONAL MATCH (coll)-[:FORM_REF]->(form:OdmFormValue) where form.oid=$neodash_select_crf
OPTIONAL MATCH (form)-[:ITEM_GROUP_REF]->(group:OdmItemGroupValue) where group.oid=$neodash_select_group
OPTIONAL MATCH (group)-[:ITEM_REF]->(item:OdmItemValue)
RETURN selection.label+'-V'+toString(coll_version.version) AS version,
       toInteger(COUNT(DISTINCT item)) AS `Item count`,
       'ITEM_COUNT' AS metric_type
ORDER BY version

//Display differences in group attributes for the groups in the form in the collection
WITH [
  {id: $neodash_coll_base_id, version: $neodash_coll_base_version_num, label: 'Base'},
  {id: $neodash_coll_comp_id, version: $neodash_coll_comp_version_num, label: 'Compare'}
] AS selections
UNWIND selections AS selection
MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)
WHERE elementId(coll) = selection.id 
  AND coll_version.version = selection.version
//Get form and its details
optional match(coll)-[r1_1:FORM_REF]->(form:OdmFormValue) where form.oid=$neodash_select_crf
// create the structure for comparing group details
//Get the groups in the form and the group details
optional match(form)-[r1_4:ITEM_GROUP_REF]->(group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot)
optional match(group)-[r2_1:HAS_DESCRIPTION]->(group_desc:OdmDescription)
optional match(group)-[r2_2:HAS_ALIAS]->(group_alias:OdmAlias)
optional match(group)-[r2_3:HAS_SDTM_DOMAIN]->(g_context:CTTermContext)-[r2_4:HAS_SELECTED_TERM]->(g_term_root:CTTermRoot)<-[r2_5:HAS_TERM_ROOT]-(domain:CTCodelistTerm)
optional match(group)-[r2_6:HAS_VENDOR_ELEMENT]->(g_ext_elem:OdmVendorElementValue)<-[r2_7:HAS_VENDOR_ELEMENT]-(g_elem_vendor_ns:OdmVendorNamespaceValue)<-[g_elem_vendor_ns_version:HAS_VERSION]-(),(g_ext_elem)<-[g_ext_elem_version:HAS_VERSION]-()
optional match(group)-[r2_8:HAS_VENDOR_ATTRIBUTE]->(g_ext_att:OdmVendorAttributeValue)<-[r2_9:HAS_VENDOR_ATTRIBUTE]-(g_att_vendor_ns:OdmVendorNamespaceValue)<-[g_att_vendor_ns_version:HAS_VERSION]-(),(g_ext_att)<-[g_ext_att_version:HAS_VERSION]-()
WITH DISTINCT
  selection.label as collection,
  coll_version,
  form,
  group,
  CASE
    WHEN
      group_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(group_alias))
            | ["alias-" + key, properties(group_alias)[key]]
          ])
    ELSE {}
  END AS aliasMap,
  CASE
    WHEN
      group_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(group_desc))
            | ["desc-" + key, properties(group_desc)[key]]
          ])
    ELSE {}
  END AS descMap,
  // Domain map
    CASE
    WHEN
      domain IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(domain))
            | ["domain-" + key, properties(domain)[key]]
          ])
    ELSE {}
  END AS domainMap,
  CASE
  WHEN g_ext_elem IS NOT NULL AND g_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(g_ext_elem)) | ["elemExt-" + key, properties(g_ext_elem)[key]+'(V'+g_ext_elem_version.version+')']])
  ELSE {}
END AS g_ext_elemMap,
CASE
  WHEN g_ext_att IS NOT NULL AND g_ext_att_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(g_ext_att)) | ["attExt-" + key, properties(g_ext_att)[key]+'(V'+g_ext_att_version.version+')']])
  ELSE {}
END AS g_ext_attMap,
CASE
  WHEN g_elem_vendor_ns IS NOT NULL AND g_elem_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(g_elem_vendor_ns)) | ["elem_nsExt-" + key, properties(g_elem_vendor_ns)[key]+'(V'+g_elem_vendor_ns_version.version+')']])
  ELSE {}
END AS g_elem_vendor_nsMap,
CASE
  WHEN g_att_vendor_ns IS NOT NULL AND g_att_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(g_att_vendor_ns)) | ["att_nsExt-" + key, properties(g_att_vendor_ns)[key]+'(V'+g_att_vendor_ns_version.version+')']])
  ELSE {}
END AS g_att_vendor_nsMap,
  coalesce(properties(group), {}) AS groupMap
WITH
  collection,
  coll_version,
  form,
  group,
 apoc.map.mergeList([groupMap, descMap, aliasMap, domainMap, g_att_vendor_nsMap, g_elem_vendor_nsMap, g_ext_attMap, g_ext_elemMap]) AS props_map
UNWIND keys(props_map) AS field
WITH DISTINCT
  form.oid AS fOID,
  group.oid as gOID,
  field,
  apoc.map.fromPairs(collect([collection, props_map[field]])) AS value_map
WITH DISTINCT
  fOID AS `CRF OID`,
  gOID as `Group OID`,
  CASE split(field, '-')[0]
  WHEN 'elem_nsExt' THEN '8ElementVendorExtNameSpace'
  WHEN 'elemExt' THEN '7ElementVendorExt'
  WHEN 'att_nsExt' THEN '6AttributeVendorExtNameSpace'
  WHEN 'attExt' THEN '5AttributeVendorExt'
  WHEN 'domain' THEN '4Domain'
  WHEN 'alias' THEN '3Alias'
  WHEN 'desc' THEN '2Description'
  ELSE '1Identification'
END AS area,
  CASE WHEN split(field, '-')[0] IN ['desc', 'alias', 'domain', 'attExt','elemExt','elem_nsExt','att_nsExt'] 
     THEN split(field, '-')[1]  
     ELSE field 
END AS `Group attribute`,  
  replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
  replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `CRF OID`, `Group OID`, area, `Group attribute`
WITH DISTINCT `CRF OID`,`Group OID`, area, `Group attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `Group OID`,substring(area,1) as Area, `Group attribute`, Base, Compare, __diff

//Display difference in item and their attributes in the select group,CRF and collection
WITH [
  {id: $neodash_coll_base_id, version: $neodash_coll_base_version_num, label: 'Base'},
  {id: $neodash_coll_comp_id, version: $neodash_coll_comp_version_num, label: 'Compare'}
] AS selections
UNWIND selections AS selection
MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)
WHERE elementId(coll) = selection.id 
  AND coll_version.version = selection.version
//Get form and its details
optional match(coll)-[r1_1:FORM_REF]->(form:OdmFormValue) where form.oid=$neodash_select_crf
optional match(form)-[r1_4:ITEM_GROUP_REF]->(group:OdmItemGroupValue) where group.oid=$neodash_select_group
  //Get the item in the group on the form and the item details
optional match(group)-[r3_1:ITEM_REF]->(item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot)
optional match(item)-[r3_2:HAS_DESCRIPTION]->(item_desc:OdmDescription)
optional match(item)-[r3_3:HAS_ALIAS]->(item_alias:OdmAlias)
optional match(item)-[r3_4:HAS_CODELIST_TERM]->(i_context:CTTermContext)-[r3_5:HAS_SELECTED_TERM]->(i_term_root:CTTermRoot)<-[r3_6:HAS_TERM_ROOT]-(item_term:CTCodelistTerm)
optional match(item)-[r3_7:HAS_VENDOR_ELEMENT]->(i_ext_elem:OdmVendorElementValue)<-[r3_8:HAS_VENDOR_ELEMENT]-(i_elem_vendor_ns:OdmVendorNamespaceValue)<-[i_elem_vendor_ns_version:HAS_VERSION]-(),(i_ext_elem)<-[i_ext_elem_version:HAS_VERSION]-()
optional match(item)-[r3_9:HAS_VENDOR_ATTRIBUTE]->(i_ext_att:OdmVendorAttributeValue)<-[r3_10:HAS_VENDOR_ATTRIBUTE]-(i_att_vendor_ns:OdmVendorNamespaceValue)<-[i_att_vendor_ns_version:HAS_VERSION]-(),(i_ext_att)<-[i_ext_att_version:HAS_VERSION]-()
WITH DISTINCT
  selection.label as collection,
  coll_version,
  form,
  group,
  item,
  CASE
    WHEN
      item_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_alias))
            | ["alias-" + key, properties(item_alias)[key]]
          ])
    ELSE {}
  END AS aliasMap,
  CASE
    WHEN
      item_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_desc))
            | ["desc-" + key, properties(item_desc)[key]]
          ])
    ELSE {}
  END AS descMap,
  // Domain map
    CASE
    WHEN
      item_term IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_term))
            | ["itemterm-" + key, properties(item_term)[key]]
          ])
    ELSE {}
  END AS itemTermMap,
CASE
  WHEN i_ext_elem IS NOT NULL AND i_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_ext_elem)) | ["elemExt-" + key, properties(i_ext_elem)[key]+'(V'+i_ext_elem_version.version+')']])
  ELSE {}
END AS i_ext_elemMap,

CASE
  WHEN i_ext_att IS NOT NULL AND i_ext_att_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_ext_att)) | ["attExt-" + key, properties(i_ext_att)[key]+'(V'+i_ext_att_version.version+')']])
  ELSE {}
END AS i_ext_attMap,

CASE
  WHEN i_elem_vendor_ns IS NOT NULL AND i_elem_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_elem_vendor_ns)) | ["elem_nsExt-" + key, properties(i_elem_vendor_ns)[key]+'(V'+i_elem_vendor_ns_version.version+')']])
  ELSE {}
END AS i_elem_vendor_nsMap,

CASE
  WHEN i_att_vendor_ns IS NOT NULL AND i_att_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_att_vendor_ns)) | ["att_nsExt-" + key, properties(i_att_vendor_ns)[key]+'(V'+i_att_vendor_ns_version.version+')']])
  ELSE {}
END AS i_att_vendor_nsMap,
  coalesce(properties(item), {}) AS itemMap
WITH 
  collection,
  coll_version,
  form,
  group,
  item,
  itemMap,
  descMap,
  aliasMap,
  i_ext_elemMap,
  i_ext_attMap,
  i_elem_vendor_nsMap,
  i_att_vendor_nsMap,
  collect(itemTermMap) as itemTermMaps
WITH 
  collection,
  coll_version,
  form,
  group,
  item,
  itemMap,
  descMap,
  aliasMap,
  i_ext_elemMap,
  i_ext_attMap,
  i_elem_vendor_nsMap,
  i_att_vendor_nsMap,
  {`itemterm-submission_value`: apoc.text.join([map IN itemTermMaps | map.`itemterm-submission_value`], ";")} AS itemTermMap
WITH collection,
  coll_version,
  form,
  group,
  item,
  apoc.map.mergeList([itemMap, descMap, aliasMap, itemTermMap, i_att_vendor_nsMap, i_elem_vendor_nsMap, i_ext_attMap, i_ext_elemMap]) AS props_map
UNWIND keys(props_map) AS field
WITH DISTINCT
  form.oid AS fOID,
  group.oid as gOID,
  item.oid as iOID,
  field,
  apoc.map.fromPairs(collect([collection, props_map[field]])) AS value_map
WITH DISTINCT
  fOID AS `CRF OID`,
  gOID as `Group OID`,
  iOID as `Item OID`,
  CASE split(field, '-')[0]
  WHEN 'elem_nsExt' THEN '8ElementVendorExtNameSpace'
  WHEN 'elemExt' THEN '7ElementVendorExt'
  WHEN 'att_nsExt' THEN '6AttributeVendorExtNameSpace'
  WHEN 'attExt' THEN '5AttributeVendorExt'
  WHEN 'itemterm' THEN '4Terms'
  WHEN 'alias' THEN '3Alias'
  WHEN 'desc' THEN '2Description'
  ELSE '1Identification'
END AS area,
  CASE WHEN split(field, '-')[0] IN ['desc', 'alias', 'itemterm', 'attExt','elemExt','elem_nsExt','att_nsExt'] 
     THEN split(field, '-')[1]  
     ELSE field 
END AS `Item attribute`,
replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `CRF OID`, `Group OID`, `Item OID`, area, `Item attribute`
WITH DISTINCT `CRF OID`,`Group OID`, `Item OID`, area, `Item attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `Item OID`,substring(area,1) as Area, `Item attribute`, Base, Compare, __diff


//**************************//
// CRF versions
//**************************//

//select BASE (or comp)
match(form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot)
WHERE $neodash_odmformvalue_oid IS NULL 
   OR $neodash_odmformvalue_oid = '' 
   OR form.oid = $neodash_odmformvalue_oid
return form.oid as OID, 
form.name as `Name`, 
form_version.version as Version, 
'Base' as Select, 
elementId(form) as __crf_id,
form_version.version as __crf_version
order by OID, Version

//View selected
MATCH (form:OdmFormValue)<-[:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
WITH CASE WHEN count(DISTINCT form_root) > 1 THEN 'Across CRF' ELSE 'Within CRF' END AS compare_type

WITH compare_type, [
  {id: $neodash_crf_base_id, version: $neodash_crf_base_version_num, label: 'Base'},
  {id: $neodash_crf_comp_id, version: $neodash_crf_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) = selection.id 
  AND form_version.version = selection.version

RETURN 
  selection.label as `CRF Selection`,
  form.oid as OID, 
  form.name as Name, 
  form_version.version as Version, 
  compare_type as `Compare Type`
ORDER BY OID, Version, `CRF Selection`


// CRF attributes versions
MATCH (form:OdmFormValue)<-[:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
WITH CASE WHEN count(DISTINCT form_root) > 1 THEN 'Across CRF' ELSE 'Within CRF' END AS compare_type

WITH compare_type, [
  {id: $neodash_crf_base_id, version: $neodash_crf_base_version_num, label: 'Base'},
  {id: $neodash_crf_comp_id, version: $neodash_crf_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) = selection.id 
  AND form_version.version = selection.version
OPTIONAL MATCH (form)-[r1_2:HAS_DESCRIPTION]->(form_desc:OdmDescription)
OPTIONAL MATCH (form)-[r1_3:HAS_ALIAS]->(form_alias:OdmAlias)
OPTIONAL MATCH (form)-[r1_4:HAS_VENDOR_ELEMENT]->(f_ext_elem:OdmVendorElementValue)<-[r1_5:HAS_VENDOR_ELEMENT]-(f_elem_vendor_ns:OdmVendorNamespaceValue)<-[f_elem_vendor_ns_version:HAS_VERSION]-(),(f_ext_elem)<-[f_ext_elem_version:HAS_VERSION]-()
OPTIONAL MATCH (form)-[r1_6:HAS_VENDOR_ATTRIBUTE]->(f_ext_att:OdmVendorAttributeValue)<-[r1_7:HAS_VENDOR_ATTRIBUTE]-(f_att_vendor_ns:OdmVendorNamespaceValue)<-[f_att_vendor_ns_version:HAS_VERSION]-(),(f_ext_att)<-[f_ext_att_version:HAS_VERSION]-()
WITH DISTINCT
  selection,
  form,
  form_version,
  CASE
    WHEN
      form_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(form_alias))
            | ["alias-" + key, properties(form_alias)[key]]
          ])
    ELSE {}
  END AS aliasMap,
  CASE
    WHEN
      form_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(form_desc))
            | ["desc-" + key, properties(form_desc)[key]]
          ])
    ELSE {}
  END AS descMap,
  CASE
  WHEN f_ext_elem IS NOT NULL AND f_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_ext_elem)) | ["elemExt-" + key, properties(f_ext_elem)[key]+'(V'+f_ext_elem_version.version+')']])
  ELSE {}
END AS f_ext_elemMap,
CASE
  WHEN f_ext_att IS NOT NULL AND f_ext_att_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_ext_att)) | ["attExt-" + key, properties(f_ext_att)[key]+'(V'+f_ext_att_version.version+')']])
  ELSE {}
END AS f_ext_attMap,
CASE
  WHEN f_elem_vendor_ns IS NOT NULL AND f_elem_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_elem_vendor_ns)) | ["elem_nsExt-" + key, properties(f_elem_vendor_ns)[key]+'(V'+f_elem_vendor_ns_version.version+')']])
  ELSE {}
END AS f_elem_vendor_nsMap,
CASE
  WHEN f_att_vendor_ns IS NOT NULL AND f_att_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(f_att_vendor_ns)) | ["att_nsExt-" + key, properties(f_att_vendor_ns)[key]+'(V'+f_att_vendor_ns_version.version+')']])
  ELSE {}
END AS f_att_vendor_nsMap,
  coalesce(properties(form), {}) AS formMap
WITH
  selection,
  form,
  form_version,
apoc.map.mergeList([formMap, descMap, aliasMap, f_att_vendor_nsMap, f_elem_vendor_nsMap, f_ext_attMap, f_ext_elemMap]) AS props_map
UNWIND keys(props_map) AS field
WITH
  form.oid AS OID,
  field,
  apoc.map.fromPairs(collect([selection.label, props_map[field]])) AS value_map
WITH
  OID AS `CRF OID`,
  CASE split(field, '-')[0]
  WHEN 'elem_nsExt' THEN '7ElementVendorExtNameSpace'
  WHEN 'elemExt' THEN '6ElementVendorExt'
  WHEN 'att_nsExt' THEN '5AttributeVendorExtNameSpace'
  WHEN 'attExt' THEN '4AttributeVendorExt'
  WHEN 'desc' THEN '2Description'
  WHEN 'alias' THEN '3Alias'
  ELSE '1Identification'
END AS area,
  CASE WHEN split(field, '-')[0] IN ['desc', 'alias', 'attExt','elemExt','elem_nsExt','att_nsExt'] 
     THEN split(field, '-')[1]  
     ELSE field 
END AS `CRF attribute`,  
  replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
  replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `CRF OID`, area, `CRF attribute`
WITH `CRF OID`,area, `CRF attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `CRF OID`,substring(area,1) as Area, `CRF attribute`, Base, Compare, __diff


//Form versions selected in collection
MATCH (form:OdmFormValue)<-[:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
WITH CASE WHEN count(DISTINCT form_root) > 1 THEN 'Across CRF' ELSE 'Within CRF' END AS compare_type

WITH compare_type, [
  {id: $neodash_crf_base_id, version: $neodash_crf_base_version_num, label: 'Base'},
  {id: $neodash_crf_comp_id, version: $neodash_crf_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) = selection.id 
  AND form_version.version = selection.version
  OPTIONAL MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)-[r1_1:FORM_REF]->(form:OdmFormValue)
 WITH distinct selection, collect(DISTINCT coll.name+'(V'+coll_version.version+')') AS coll
 WITH apoc.map.fromPairs(collect([selection.label, coll])) AS data
WITH data, 
     CASE WHEN size(data.Base) > size(data.Compare) 
          THEN size(data.Base) 
          ELSE size(data.Compare) 
     END AS maxSize
UNWIND range(0, maxSize - 1) AS idx
RETURN CASE WHEN idx < size(data.Base) THEN data.Base[idx] END AS Base,
       CASE WHEN idx < size(data.Compare) THEN data.Compare[idx] END AS Compare


  //CRF version comparison - group count
MATCH (form:OdmFormValue)<-[:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
WITH CASE WHEN count(DISTINCT form_root) > 1 THEN 'Across CRF' ELSE 'Within CRF' END AS compare_type

WITH compare_type, [
  {id: $neodash_crf_base_id, version: $neodash_crf_base_version_num, label: 'Base'},
  {id: $neodash_crf_comp_id, version: $neodash_crf_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) = selection.id 
  AND form_version.version = selection.version
WITH selection,form, form_version where form_version.version in[$neodash_crf_base_version_num, $neodash_crf_comp_version_num]
OPTIONAL MATCH (form)-[:ITEM_GROUP_REF]->(group:OdmItemGroupValue)
RETURN  
      selection.label+'-V'+toString(form_version.version) AS version,
        toInteger(COUNT(DISTINCT group)) AS `Group count`,
        'GROUP_COUNT' AS metric_type

// CRF group attribute details - differences
MATCH (form:OdmFormValue)<-[:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
WITH CASE WHEN count(DISTINCT form_root) > 1 THEN 'Across CRF' ELSE 'Within CRF' END AS compare_type

WITH compare_type, [
  {id: $neodash_crf_base_id, version: $neodash_crf_base_version_num, label: 'Base'},
  {id: $neodash_crf_comp_id, version: $neodash_crf_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) = selection.id 
  AND form_version.version = selection.version
  //Get the groups in the form and the group details
optional match(form)-[r1_4:ITEM_GROUP_REF]->(group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot)
optional match(group)-[r2_1:HAS_DESCRIPTION]->(group_desc:OdmDescription)
optional match(group)-[r2_2:HAS_ALIAS]->(group_alias:OdmAlias)
optional match(group)-[r2_3:HAS_SDTM_DOMAIN]->(g_context:CTTermContext)-[r2_4:HAS_SELECTED_TERM]->(g_term_root:CTTermRoot)<-[r2_5:HAS_TERM_ROOT]-(domain:CTCodelistTerm)
WITH DISTINCT
  selection.label AS form_compare,
  form,
  group,
  CASE
    WHEN
      group_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(group_alias))
            | ["alias-" + key, properties(group_alias)[key]]
          ])
    ELSE null
  END AS aliasMap,
  CASE
    WHEN
      group_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(group_desc))
            | ["desc-" + key, properties(group_desc)[key]]
          ])
    ELSE null
  END AS descMap,
  // Domain map
    CASE
    WHEN
      domain IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(domain))
            | ["domain-" + key, properties(domain)[key]]
          ])
    ELSE null
  END AS domainMap,
  properties(group) AS groupMap
WITH
  form_compare,
  form,
  group,
  apoc.map.merge(groupMap, apoc.map.merge(descMap, apoc.map.merge(aliasMap,domainMap))) AS props_map
WITH form_compare, form, group, props_map
UNWIND keys(props_map) AS field
WITH DISTINCT
  form.oid AS fOID,
  group.oid as gOID,
  field,
  apoc.map.fromPairs(collect([form_compare, props_map[field]])) AS value_map
WITH DISTINCT
  fOID AS `CRF OID`,
  gOID as `Group OID`,
  CASE WHEN field contains 'desc-' THEN '2Description' ELSE 
  CASE WHEN field contains 'alias-' THEN '3Alias' ELSE 
  CASE WHEN field contains 'domain-' THEN '4Domain' ELSE '1Identification' END END END as area,
  CASE WHEN (field contains 'desc-') OR (field contains 'alias-') OR (field contains 'domain-') THEN split(field, '-')[1]  ELSE field END AS `Group attribute`,
  replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
  replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `CRF OID`, `Group OID`, area, `Group attribute`
WITH DISTINCT `CRF OID`,`Group OID`, area, `Group attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `Group OID`,substring(area,1) as Area, `Group attribute`, Base, Compare, __diff

// CRF Item count

MATCH (form:OdmFormValue)<-[:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
WITH CASE WHEN count(DISTINCT form_root) > 1 THEN 'Across CRF' ELSE 'Within CRF' END AS compare_type

WITH compare_type, [
  {id: $neodash_crf_base_id, version: $neodash_crf_base_version_num, label: 'Base'},
  {id: $neodash_crf_comp_id, version: $neodash_crf_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) = selection.id 
  AND form_version.version = selection.version
OPTIONAL MATCH (form)-[:ITEM_GROUP_REF]->(group:OdmItemGroupValue) where group.oid=$neodash_select_group_2
OPTIONAL MATCH (group)-[:ITEM_REF]->(item:OdmItemValue)
RETURN  
      selection.label+'-V'+toString(form_version.version) AS version,
        toInteger(COUNT(DISTINCT item)) AS `Item count`,
        'ITEM_COUNT' AS metric_type
ORDER BY version

//CRF - select group - filter
MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-
  (form_root:OdmFormRoot) where elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
OPTIONAL MATCH (form)-[:ITEM_GROUP_REF]->(group:OdmItemGroupValue)
WHERE toLower(toString(group.`oid`)) CONTAINS toLower($input) 
RETURN DISTINCT group.`oid` as value,  group.`oid` as display ORDER BY size(toString(value)) ASC LIMIT 100

//CRF display item attribute differences in group selected
MATCH (form:OdmFormValue)<-[:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) IN [$neodash_crf_base_id, $neodash_crf_comp_id]
WITH CASE WHEN count(DISTINCT form_root) > 1 THEN 'Across CRF' ELSE 'Within CRF' END AS compare_type

WITH compare_type, [
  {id: $neodash_crf_base_id, version: $neodash_crf_base_version_num, label: 'Base'},
  {id: $neodash_crf_comp_id, version: $neodash_crf_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (form:OdmFormValue)<-[form_version:HAS_VERSION]-(form_root:OdmFormRoot) 
WHERE elementId(form) = selection.id 
  AND form_version.version = selection.version
  //Get the item in the group on the form and the item details
optional match(group)-[r3_1:ITEM_REF]->(item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot)
optional match(item)-[r3_2:HAS_DESCRIPTION]->(item_desc:OdmDescription)
optional match(item)-[r3_3:HAS_ALIAS]->(item_alias:OdmAlias)
optional match(item)-[r3_4:HAS_CODELIST_TERM]->(i_context:CTTermContext)-[r3_5:HAS_SELECTED_TERM]->(i_term_root:CTTermRoot)<-[r3_6:HAS_TERM_ROOT]-(item_term:CTCodelistTerm)
WITH DISTINCT
  selection.label as form_compare,
  form_version,
  form,
  group,
  item,
  CASE
    WHEN
      item_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_alias))
            | ["alias-" + key, properties(item_alias)[key]]
          ])
    ELSE null
  END AS aliasMap,
  CASE
    WHEN
      item_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_desc))
            | ["desc-" + key, properties(item_desc)[key]]
          ])
    ELSE null
  END AS descMap,
  // Domain map
    CASE
    WHEN
      item_term IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_term))
            | ["itemterm-" + key, properties(item_term)[key]]
          ])
    ELSE null
  END AS itemTermMap,
  properties(item) AS itemMap
WITH 
  form_compare,
  form_version,
  form,
  group,
  item,
  itemMap,
  descMap,
  aliasMap,
  collect(itemTermMap) as itemTermMaps
WITH 
  form_compare,
  form_version,
  form,
  group,
  item,
  itemMap,
  descMap,
  aliasMap,
  {`itemterm-submission_value`: apoc.text.join([map IN itemTermMaps | map.`itemterm-submission_value`], ";")} AS itemTermMap
WITH form_compare,
  form_version,
  form,
  group,
  item,
  apoc.map.merge(itemMap, apoc.map.merge(descMap, apoc.map.merge(aliasMap,itemTermMap))) AS props_map
WITH form_compare, form, group, item, props_map
UNWIND keys(props_map) AS field
WITH DISTINCT
  form.oid AS fOID,
  group.oid as gOID,
  item.oid as iOID,
  field,
  apoc.map.fromPairs(collect([form_compare, props_map[field]])) AS value_map
WITH DISTINCT
  fOID AS `CRF OID`,
  gOID as `Group OID`,
  iOID as `Item OID`,
  CASE WHEN field contains 'desc-' THEN '2Description' ELSE 
  CASE WHEN field contains 'alias-' THEN '3Alias' ELSE 
  CASE WHEN field contains 'itemterm-' THEN '4Terms' ELSE '1Identification' END END END as area,
  CASE WHEN (field contains 'desc-') OR (field contains 'alias-') OR (field contains 'domain-') OR (field contains 'itemterm-') THEN split(field, '-')[1]  ELSE field END AS `Item attribute`,
  replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
  replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `CRF OID`, `Group OID`, `Item OID`, area, `Item attribute`
WITH DISTINCT `CRF OID`,`Group OID`, `Item OID`, area, `Item attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `Item OID`,substring(area,1) as Area, `Item attribute`, Base, Compare, __diff

//**************************//
// Group versions
//**************************//

//select Base (or Compare)
match(group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot)
WHERE $neodash_odmgroupvalue_oid IS NULL 
   OR $neodash_odmgroupvalue_oid = '' 
   OR group.oid = $neodash_odmgroupvalue_oid
return group.oid as OID, 
group.name as `Name`, 
group_version.version as Version, 
'Base' as Select, 
elementId(group) as __group_id,
group_version.version as __group_version
order by OID, Version

// Selected group value versions
MATCH (group:OdmItemGroupValue)<-[:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) IN [$neodash_group_base_id, $neodash_group_comp_id]
WITH CASE WHEN count(DISTINCT group_root) > 1 THEN 'Across Group' ELSE 'Within Group' END AS compare_type

WITH compare_type, [
  {id: $neodash_group_base_id, version: $neodash_group_base_version_num, label: 'Base'},
  {id: $neodash_group_comp_id, version: $neodash_group_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) = selection.id 
  AND group_version.version = selection.version

RETURN 
  selection.label as `Group Selection`,
  group.oid as OID, 
  group.name as Name, 
  group_version.version as Version, 
  compare_type as `Compare Type`
ORDER BY OID, Version, `Group Selection`

//Group in Forms and Collections
MATCH (group:OdmItemGroupValue)<-[:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) IN [$neodash_group_base_id, $neodash_group_comp_id]
WITH CASE WHEN count(DISTINCT group_root) > 1 THEN 'Across Group' ELSE 'Within Group' END AS compare_type

WITH compare_type, [
  {id: $neodash_group_base_id, version: $neodash_group_base_version_num, label: 'Base'},
  {id: $neodash_group_comp_id, version: $neodash_group_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) = selection.id 
  AND group_version.version = selection.version
OPTIONAL MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)-[r1_1:FORM_REF]->(form:OdmFormValue)-[r1_4:ITEM_GROUP_REF]->(group)
WITH DISTINCT selection.label as group_compare, collect(DISTINCT coll.name+'-V'+coll_version.version) AS coll
WITH apoc.map.fromPairs(collect([group_compare, coll])) AS data
WITH data, 
     CASE WHEN size(data.Base) > size(data.Compare) 
          THEN size(data.Base) 
          ELSE size(data.Compare) 
     END AS maxSize
UNWIND CASE WHEN maxSize IS NULL OR maxSize = 0 
            THEN [0] 
            ELSE range(0, maxSize - 1) 
       END AS idx
RETURN CASE WHEN maxSize > 0 AND idx < size(data.Base) THEN data.Base[idx] END AS Base,
       CASE WHEN maxSize > 0 AND idx < size(data.Compare) THEN data.Compare[idx] END AS Compare

//Group attributes differences
MATCH (group:OdmItemGroupValue)<-[:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) IN [$neodash_group_base_id, $neodash_group_comp_id]
WITH CASE WHEN count(DISTINCT group_root) > 1 THEN 'Across Group' ELSE 'Within Group' END AS compare_type

WITH compare_type, [
  {id: $neodash_group_base_id, version: $neodash_group_base_version_num, label: 'Base'},
  {id: $neodash_group_comp_id, version: $neodash_group_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) = selection.id 
  AND group_version.version = selection.version
OPTIONAL MATCH (group)-[r1_2:HAS_DESCRIPTION]->(group_desc:OdmDescription)
OPTIONAL MATCH (group)-[r1_3:HAS_ALIAS]->(group_alias:OdmAlias)
WITH DISTINCT
  selection.label as group_compare,
  group,
  group_version,
  CASE
    WHEN
      group_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(group_alias))
            | ["alias-" + key, properties(group_alias)[key]]
          ])
    ELSE null
  END AS aliasMap,
  CASE
    WHEN
      group_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(group_desc))
            | ["desc-" + key, properties(group_desc)[key]]
          ])
    ELSE null
  END AS descMap,
  properties(group) AS groupMap
WITH
  group_compare,
  group,
  group_version,
  apoc.map.merge(groupMap, apoc.map.merge(descMap, aliasMap)) AS props_map
WITH group_compare,
  group,
  group_version, props_map
UNWIND keys(props_map) AS field
WITH
  group.oid AS OID,
  field,
  apoc.map.fromPairs(collect([group_compare, props_map[field]])) AS value_map
WITH
  OID AS `Group OID`,
  CASE WHEN field contains 'desc-' THEN '2Description' ELSE 
  CASE WHEN field contains 'alias-' THEN '3Alias' ELSE '1Identification' END END as area,
  CASE WHEN (field contains 'desc-') OR (field contains 'alias-') THEN split(field, '-')[1]  ELSE field END AS `Group attribute`,
  replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
  replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `Group OID`, area, `Group attribute`
WITH `Group OID`,area, `Group attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `Group OID`,substring(area,1) as Area, `Group attribute`, Base, Compare, __diff

//item attribute differences in the selected groups
MATCH (group:OdmItemGroupValue)<-[:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) IN [$neodash_group_base_id, $neodash_group_comp_id]
WITH CASE WHEN count(DISTINCT group_root) > 1 THEN 'Across Group' ELSE 'Within Group' END AS compare_type

WITH compare_type, [
  {id: $neodash_group_base_id, version: $neodash_group_base_version_num, label: 'Base'},
  {id: $neodash_group_comp_id, version: $neodash_group_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) = selection.id 
  AND group_version.version = selection.version
  //Get the item in the group on the form and the item details
optional match(group)-[r3_1:ITEM_REF]->(item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot)
optional match(item)-[r3_2:HAS_DESCRIPTION]->(item_desc:OdmDescription)
optional match(item)-[r3_3:HAS_ALIAS]->(item_alias:OdmAlias)
optional match(item)-[r3_4:HAS_CODELIST_TERM]->(i_context:CTTermContext)-[r3_5:HAS_SELECTED_TERM]->(i_term_root:CTTermRoot)<-[r3_6:HAS_TERM_ROOT]-(item_term:CTCodelistTerm)
WITH DISTINCT
  selection.label as group_compare,
  group_version,
  group,
  item,
  CASE
    WHEN
      item_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_alias))
            | ["alias-" + key, properties(item_alias)[key]]
          ])
    ELSE null
  END AS aliasMap,
  CASE
    WHEN
      item_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_desc))
            | ["desc-" + key, properties(item_desc)[key]]
          ])
    ELSE null
  END AS descMap,
  // Domain map
    CASE
    WHEN
      item_term IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_term))
            | ["itemterm-" + key, properties(item_term)[key]]
          ])
    ELSE null
  END AS itemTermMap,
  properties(item) AS itemMap
WITH 
  group_compare,
  group_version,
  group,
  item,
  itemMap,
  descMap,
  aliasMap,
  collect(itemTermMap) as itemTermMaps
WITH 
  group_compare,
  group_version,
  group,
  item,
  itemMap,
  descMap,
  aliasMap,
  {`itemterm-submission_value`: apoc.text.join([map IN itemTermMaps | map.`itemterm-submission_value`], ";")} AS itemTermMap
WITH group_compare,
  group_version,
  group,
  item,
  apoc.map.merge(itemMap, apoc.map.merge(descMap, apoc.map.merge(aliasMap,itemTermMap))) AS props_map
WITH group_compare,
  group_version,
  group,
  item, props_map
UNWIND keys(props_map) AS field
WITH DISTINCT
  group.oid as gOID,
  item.oid as iOID,
  field,
  apoc.map.fromPairs(collect([group_compare, props_map[field]])) AS value_map
WITH DISTINCT
  gOID as `Group OID`,
  iOID as `Item OID`,
  CASE WHEN field contains 'desc-' THEN '2Description' ELSE 
  CASE WHEN field contains 'alias-' THEN '3Alias' ELSE 
  CASE WHEN field contains 'itemterm-' THEN '4Terms' ELSE '1Identification' END END END as area,
  CASE WHEN (field contains 'desc-') OR (field contains 'alias-') OR (field contains 'domain-') OR (field contains 'itemterm-') THEN split(field, '-')[1]  ELSE field END AS `Item attribute`,
  replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
  replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `Group OID`, `Item OID`, area, `Item attribute`
WITH DISTINCT `Group OID`, `Item OID`, area, `Item attribute`, Base, Compare, 
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff 
RETURN `Item OID`,substring(area,1) as Area, `Item attribute`, Base, Compare, __diff

//Count of items in the group versions
MATCH (group:OdmItemGroupValue)<-[:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) IN [$neodash_group_base_id, $neodash_group_comp_id]
WITH CASE WHEN count(DISTINCT group_root) > 1 THEN 'Across Group' ELSE 'Within Group' END AS compare_type

WITH compare_type, [
  {id: $neodash_group_base_id, version: $neodash_group_base_version_num, label: 'Base'},
  {id: $neodash_group_comp_id, version: $neodash_group_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (group:OdmItemGroupValue)<-[group_version:HAS_VERSION]-(group_root:OdmItemGroupRoot) 
WHERE elementId(group) = selection.id 
  AND group_version.version = selection.version
WITH selection.label as group_compare,group, group_version where selection.version in[$neodash_group_base_version_num, $neodash_group_comp_version_num]
OPTIONAL MATCH (group)-[:ITEM_REF]->(item:OdmItemValue)
RETURN  
      group_compare+'-V'+toString(group_version.version) AS version,
        toInteger(COUNT(DISTINCT item)) AS `Item count`,
        'ITEM_COUNT' AS metric_type
ORDER BY version

//**************************//
// ITEM versions
//**************************//

//select BASE (or comp)
match(item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot)
WHERE $neodash_odmitemvalue_oid IS NULL 
   OR $neodash_odmitemvalue_oid = '' 
   OR item.oid = $neodash_odmitemvalue_oid
return item.oid as OID, 
item.name as `Name`, 
item_version.version as Version, 
'Base' as Select, 
elementId(item) as __item_id,
item_version.version as __item_version
order by OID, Version

//Seleted Items for compare
MATCH (item:OdmItemValue)<-[:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) IN [$neodash_item_base_id, $neodash_item_comp_id]
WITH CASE WHEN count(DISTINCT item_root) > 1 THEN 'Across Item' ELSE 'Within Item' END AS compare_type

WITH compare_type, [
  {id: $neodash_item_base_id, version: $neodash_item_base_version_num, label: 'Base'},
  {id: $neodash_item_comp_id, version: $neodash_item_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) = selection.id 
  AND item_version.version = selection.version

RETURN 
  selection.label as `Item Selection`,
  item.oid as OID, 
  item.name as Name, 
  item_version.version as Version, 
  compare_type as `Compare Type`
ORDER BY OID, Version, `Item Selection`

//Item attribute differences
MATCH (item:OdmItemValue)<-[:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) IN [$neodash_item_base_id, $neodash_item_comp_id]
WITH CASE WHEN count(DISTINCT item_root) > 1 THEN 'Across Item' ELSE 'Within Item' END AS compare_type

WITH compare_type, [
  {id: $neodash_item_base_id, version: $neodash_item_base_version_num, label: 'Base'},
  {id: $neodash_item_comp_id, version: $neodash_item_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection

MATCH (item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) = selection.id 
  AND item_version.version = selection.version
optional match(item)-[r3_2:HAS_DESCRIPTION]->(item_desc:OdmDescription)
optional match(item)-[r3_3:HAS_ALIAS]->(item_alias:OdmAlias)
optional match(item)-[r3_4:HAS_CODELIST_TERM]->(i_context:CTTermContext)-[r3_5:HAS_SELECTED_TERM]->(i_term_root:CTTermRoot)<-[r3_6:HAS_TERM_ROOT]-(item_term:CTCodelistTerm)
optional match(item)-[r3_7:HAS_VENDOR_ELEMENT]->(i_ext_elem:OdmVendorElementValue)<-[r3_8:HAS_VENDOR_ELEMENT]-(i_elem_vendor_ns:OdmVendorNamespaceValue)<-[i_elem_vendor_ns_version:HAS_VERSION]-(),(i_ext_elem)<-[i_ext_elem_version:HAS_VERSION]-()
optional match(item)-[value1:HAS_VENDOR_ATTRIBUTE]->(i_ext_att:OdmVendorAttributeValue)<-[r3_10:HAS_VENDOR_ATTRIBUTE]-(i_att_vendor_ns:OdmVendorNamespaceValue)<-[i_att_vendor_ns_version:HAS_VERSION]-(),(i_ext_att)<-[i_ext_att_version:HAS_VERSION]-()
optional match(item)-[r3_11:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(i_att_val:OdmVendorAttributeValue)<-[r3_12:HAS_VENDOR_ATTRIBUTE]-(i_ext_elem)
WITH DISTINCT
  selection.label as item_compare,
  item,
  value1,
  CASE
    WHEN
      item_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_alias))
            | ["alias-" + key, properties(item_alias)[key]]
          ])
    ELSE {}
  END AS aliasMap,
  CASE
    WHEN
      item_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_desc))
            | ["desc-" + key, properties(item_desc)[key]]
          ])
    ELSE {}
  END AS descMap,
  // Domain map
    CASE
    WHEN
      item_term IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_term))
            | ["itemterm-" + key, properties(item_term)[key]]
          ])
    ELSE {}
  END AS itemTermMap,
CASE
  WHEN i_ext_elem IS NOT NULL AND i_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_ext_elem)) | ["elemExt-" + key, properties(i_ext_elem)[key]+'(V'+i_ext_elem_version.version+')']])
  ELSE {}
END AS i_ext_elemMap,
CASE
  WHEN i_ext_att IS NOT NULL AND i_ext_att_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_ext_att)) | ["attExt-" + key, properties(i_ext_att)[key]+'(V'+i_ext_att_version.version+')']])
  ELSE {}
END AS i_ext_attMap,
CASE
  WHEN i_att_val IS NOT NULL AND i_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_att_val)) | ["elem_attExt-" + key, properties(i_att_val)[key]+'(V'+i_ext_elem_version.version+')']])
  ELSE {}
END AS i_ext_attMap2,
CASE
  WHEN i_elem_vendor_ns IS NOT NULL AND i_elem_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_elem_vendor_ns)) | ["elem_nsExt-" + key, properties(i_elem_vendor_ns)[key]+'(V'+i_elem_vendor_ns_version.version+')']])
  ELSE {}
END AS i_elem_vendor_nsMap,
CASE
  WHEN i_att_vendor_ns IS NOT NULL AND i_att_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_att_vendor_ns)) | ["att_nsExt-" + key, properties(i_att_vendor_ns)[key]+'(V'+i_att_vendor_ns_version.version+')']])
  ELSE {}
END AS i_att_vendor_nsMap,
  coalesce(properties(item), {}) AS itemMap,
  coalesce(properties(value1), {}) AS value1Map
WITH
  item_compare,
  item,
  itemMap,
  descMap,
  aliasMap,
  i_ext_elemMap,
  i_ext_attMap,
  i_elem_vendor_nsMap,
  i_att_vendor_nsMap,
  i_ext_attMap2,
  collect(distinct itemTermMap) as itemTermMaps,
  collect(distinct value1Map) as value_i_ext_attMap
WITH
  item_compare,
  item,
  itemMap,
  descMap,
  aliasMap,
  i_ext_elemMap,
  i_ext_attMap,
  i_elem_vendor_nsMap,
  i_att_vendor_nsMap,
  i_ext_attMap2,
  {`itemterm-submission_value`: apoc.text.join([map IN itemTermMaps | map.`itemterm-submission_value`], ";")} AS itemTermMap,
  {`attExt-value`: apoc.text.join([map IN value_i_ext_attMap | map.value], ";")} AS value_i_ext_attMap
WITH
  item_compare,
  item,
  apoc.map.mergeList([itemMap, descMap, aliasMap, itemTermMap, i_att_vendor_nsMap, i_elem_vendor_nsMap, i_ext_attMap, i_ext_elemMap,i_ext_attMap2,value_i_ext_attMap]) AS props_map
UNWIND keys(props_map) AS field
WITH DISTINCT
  item.oid as iOID,
  field,
  apoc.map.fromPairs(collect([item_compare, props_map[field]])) AS value_map
WITH DISTINCT
  iOID as `Item OID`,
  CASE split(field, '-')[0]
  WHEN 'elem_nsExt' THEN '9VendorExt(NameSpace for Element)'
  WHEN 'elem_attExt' THEN '8VendorExt(Attribute for Element)'
  WHEN 'elemExt' THEN '7VendorExt(Element)'
  WHEN 'att_nsExt' THEN '6VendorExt(NameSpace for Attribute)'
  WHEN 'attExt' THEN '5VendorExt(Attribute)'
  WHEN 'itemterm' THEN '4Terms'
  WHEN 'alias' THEN '3Alias'
  WHEN 'desc' THEN '2Description'
  ELSE '1Identification'
END AS area,
  CASE WHEN split(field, '-')[0] IN ['desc', 'alias', 'itemterm', 'attExt','elem_attExt','elemExt','elem_nsExt','att_nsExt']
     THEN split(field, '-')[1]  
     ELSE field
END AS `Item attribute`,
replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `Item OID`, area, `Item attribute`
WITH DISTINCT `Item OID`, area, `Item attribute`, Base, Compare,
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff
RETURN `Item OID`,substring(area,1) as Area, `Item attribute`, Base, Compare, __diff

//Item in collection
MATCH (item:OdmItemValue)<-[:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) IN [$neodash_item_base_id, $neodash_item_comp_id]
WITH CASE WHEN count(DISTINCT item_root) > 1 THEN 'Across Item' ELSE 'Within Item' END AS compare_type

WITH compare_type, [
  {id: $neodash_item_base_id, version: $neodash_item_base_version_num, label: 'Base'},
  {id: $neodash_item_comp_id, version: $neodash_item_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) = selection.id 
  AND item_version.version = selection.version
OPTIONAL MATCH (coll_root:OdmStudyEventRoot)-[coll_version:HAS_VERSION]->(coll:OdmStudyEventValue)-[r1_1:FORM_REF]->(form:OdmFormValue)-[r1_4:ITEM_GROUP_REF]->(group:OdmItemGroupValue)-[r3_1:ITEM_REF]->(item)
WITH selection.label as item_compare, coll.name as coll_name, coll_version.version as coll_version order by coll_name, coll_version
WITH DISTINCT item_compare, collect(DISTINCT coll_name+'(V'+coll_version+')') AS coll
WITH apoc.map.fromPairs(collect([item_compare, coll])) AS data
WITH data, 
     CASE WHEN size(data.Base) > size(data.Compare) 
          THEN size(data.Base) 
          ELSE size(data.Compare) 
     END AS maxSize
UNWIND CASE WHEN maxSize IS NULL OR maxSize = 0 
            THEN [0] 
            ELSE range(0, maxSize - 1) 
       END AS idx
RETURN CASE WHEN maxSize > 0 AND idx < size(data.Base) THEN data.Base[idx] END AS Base,
       CASE WHEN maxSize > 0 AND idx < size(data.Compare) THEN data.Compare[idx] END AS Compare

//Item in CRFs
MATCH (item:OdmItemValue)<-[:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) IN [$neodash_item_base_id, $neodash_item_comp_id]
WITH CASE WHEN count(DISTINCT item_root) > 1 THEN 'Across Item' ELSE 'Within Item' END AS compare_type

WITH compare_type, [
  {id: $neodash_item_base_id, version: $neodash_item_base_version_num, label: 'Base'},
  {id: $neodash_item_comp_id, version: $neodash_item_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) = selection.id 
  AND item_version.version = selection.version
OPTIONAL MATCH ()-[form_version:HAS_VERSION]->(form:OdmFormValue)-[r1_4:ITEM_GROUP_REF]->(group:OdmItemGroupValue)-[r3_1:ITEM_REF]->(item)
WITH selection.label as item_compare, form.name as name, form_version.version as version order by name, version
WITH DISTINCT item_compare, collect(DISTINCT name+'(V'+version+')') AS form
WITH apoc.map.fromPairs(collect([item_compare, form])) AS data
WITH data, 
     CASE WHEN size(data.Base) > size(data.Compare) 
          THEN size(data.Base) 
          ELSE size(data.Compare) 
     END AS maxSize
UNWIND CASE WHEN maxSize IS NULL OR maxSize = 0 
            THEN [0] 
            ELSE range(0, maxSize - 1) 
       END AS idx
RETURN CASE WHEN maxSize > 0 AND idx < size(data.Base) THEN data.Base[idx] END AS Base,
       CASE WHEN maxSize > 0 AND idx < size(data.Compare) THEN data.Compare[idx] END AS Compare

// Item in groups
MATCH (item:OdmItemValue)<-[:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) IN [$neodash_item_base_id, $neodash_item_comp_id]
WITH CASE WHEN count(DISTINCT item_root) > 1 THEN 'Across Item' ELSE 'Within Item' END AS compare_type

WITH compare_type, [
  {id: $neodash_item_base_id, version: $neodash_item_base_version_num, label: 'Base'},
  {id: $neodash_item_comp_id, version: $neodash_item_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) = selection.id 
  AND item_version.version = selection.version
OPTIONAL MATCH ()-[group_version:HAS_VERSION]->(group:OdmItemGroupValue)-[r3_1:ITEM_REF]->(item)
WITH selection.label as item_compare, group.name as name, group_version.version as version order by name, version
WITH DISTINCT item_compare, collect(DISTINCT name+'(V'+version+')') AS group
WITH apoc.map.fromPairs(collect([item_compare, group])) AS data
WITH data, 
     CASE WHEN size(data.Base) > size(data.Compare) 
          THEN size(data.Base) 
          ELSE size(data.Compare) 
     END AS maxSize
UNWIND CASE WHEN maxSize IS NULL OR maxSize = 0 
            THEN [0] 
            ELSE range(0, maxSize - 1) 
       END AS idx
RETURN CASE WHEN maxSize > 0 AND idx < size(data.Base) THEN data.Base[idx] END AS Base,
       CASE WHEN maxSize > 0 AND idx < size(data.Compare) THEN data.Compare[idx] END AS Compare


//With multipe props for vendor extensions
MATCH (item:OdmItemValue)<-[:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) IN [$neodash_item_base_id, $neodash_item_comp_id]
WITH CASE WHEN count(DISTINCT item_root) > 1 THEN 'Across Item' ELSE 'Within Item' END AS compare_type

WITH compare_type, [
  {id: $neodash_item_base_id, version: $neodash_item_base_version_num, label: 'Base'},
  {id: $neodash_item_comp_id, version: $neodash_item_comp_version_num, label: 'Compare'}
] AS selections

UNWIND selections AS selection
MATCH (item:OdmItemValue)<-[item_version:HAS_VERSION]-(item_root:OdmItemRoot) 
WHERE elementId(item) = selection.id 
  AND item_version.version = selection.version
optional match(item)-[r3_2:HAS_DESCRIPTION]->(item_desc:OdmDescription)
optional match(item)-[r3_3:HAS_ALIAS]->(item_alias:OdmAlias)
optional match(item)-[r3_4:HAS_CODELIST_TERM]->(i_context:CTTermContext)-[r3_5:HAS_SELECTED_TERM]->(i_term_root:CTTermRoot)<-[r3_6:HAS_TERM_ROOT]-(item_term:CTCodelistTerm)
optional match(item)-[r3_7:HAS_VENDOR_ELEMENT]->(i_ext_elem:OdmVendorElementValue)<-[r3_8:HAS_VENDOR_ELEMENT]-(i_elem_vendor_ns:OdmVendorNamespaceValue)<-[i_elem_vendor_ns_version:HAS_VERSION]-(),(i_ext_elem)<-[i_ext_elem_version:HAS_VERSION]-()
optional match(item)-[value1:HAS_VENDOR_ATTRIBUTE]->(i_ext_att:OdmVendorAttributeValue)<-[r3_10:HAS_VENDOR_ATTRIBUTE]-(i_att_vendor_ns:OdmVendorNamespaceValue)<-[i_att_vendor_ns_version:HAS_VERSION]-(),(i_ext_att)<-[i_ext_att_version:HAS_VERSION]-()
optional match(item)-[value2:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(i_att_val:OdmVendorAttributeValue)<-[r3_12:HAS_VENDOR_ATTRIBUTE]-(i_ext_elem)
WITH DISTINCT
  selection.label as item_compare,
  item,
  value1,
  CASE
    WHEN
      item_alias IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_alias))
            | ["alias-" + key, properties(item_alias)[key]]
          ])
    ELSE {}
  END AS aliasMap,
  CASE
    WHEN
      item_desc IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_desc))
            | ["desc-" + key, properties(item_desc)[key]]
          ])
    ELSE {}
  END AS descMap,
  // Domain map
    CASE
    WHEN
      item_term IS NOT NULL
      THEN
        apoc.map.fromPairs(
          [
            key IN keys(properties(item_term))
            | ["itemterm-" + key, properties(item_term)[key]]
          ])
    ELSE {}
  END AS itemTermMap,
CASE
  WHEN i_ext_elem IS NOT NULL AND i_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_ext_elem)) | ["elemExt-" + key, properties(i_ext_elem)[key]+'(V'+i_ext_elem_version.version+')']])
  ELSE {}
END AS i_ext_elemMap,
CASE
  WHEN i_ext_att IS NOT NULL AND i_ext_att_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_ext_att)) | ["attExt-" + key, properties(i_ext_att)[key]+'(V'+i_ext_att_version.version+')']])
  ELSE {}
END AS i_ext_attMap,
CASE
  WHEN i_att_val IS NOT NULL AND i_ext_elem_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_att_val)) | ["elem_attExt-" + key, properties(i_att_val)[key]+'(V'+i_ext_elem_version.version+')']])
  ELSE {}
END AS i_ext_attMap2,
CASE
  WHEN i_elem_vendor_ns IS NOT NULL AND i_elem_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_elem_vendor_ns)) | ["elem_nsExt-" + key, properties(i_elem_vendor_ns)[key]+'(V'+i_elem_vendor_ns_version.version+')']])
  ELSE {}
END AS i_elem_vendor_nsMap,
CASE
  WHEN i_att_vendor_ns IS NOT NULL AND i_att_vendor_ns_version IS NOT NULL
    THEN apoc.map.fromPairs([key IN keys(properties(i_att_vendor_ns)) | ["att_nsExt-" + key, properties(i_att_vendor_ns)[key]+'(V'+i_att_vendor_ns_version.version+')']])
  ELSE {}
END AS i_att_vendor_nsMap,
CASE
  WHEN properties(value1) IS NOT NULL 
    THEN apoc.map.fromPairs([key IN keys(properties(value1)) | ["attExt-" + key, properties(value1)[key]]])
  ELSE {}
END AS value1Map,
CASE
  WHEN properties(value2) IS NOT NULL 
    THEN apoc.map.fromPairs([key IN keys(properties(value2)) | ["elem_attExt-" + key, properties(value2)[key]]])
  ELSE {}
END AS value2Map,
  coalesce(properties(item), {}) AS itemMap
WITH
  item_compare,
  item,
  itemMap,
  descMap,
  aliasMap,
  i_ext_elemMap,
  apoc.map.merge(i_ext_attMap,value1Map) as value_i_ext_attMap,
  i_elem_vendor_nsMap,
  i_att_vendor_nsMap,
  apoc.map.merge(i_ext_attMap2,value2Map) as value_i_elem_attMap2,
  collect(distinct itemTermMap) as itemTermMaps
WITH
  item_compare,
  item,
  collect(itemMap) as itemMap,
  collect(descMap) as descMap,
  collect(aliasMap) as aliasMap,
  collect(i_ext_elemMap) as i_ext_elemMap,
  collect(i_elem_vendor_nsMap) as i_elem_vendor_nsMap,
  collect(i_att_vendor_nsMap) as i_att_vendor_nsMap,
  collect(value_i_ext_attMap) as value_i_ext_attMap ,
  collect(value_i_elem_attMap2) as value_i_elem_attMap2 ,
  collect({`itemterm-submission_value`: apoc.text.join([map IN itemTermMaps | map.`itemterm-submission_value`], ";")}) AS itemTermMap
WITH
  item_compare,
  item,
  itemMap+descMap+aliasMap+itemTermMap+i_att_vendor_nsMap+i_elem_vendor_nsMap+i_ext_elemMap+value_i_elem_attMap2+value_i_ext_attMap AS props_maps
UNWIND props_maps as props_map
UNWIND keys(props_map) AS field
WITH DISTINCT
  item.oid as iOID,
  field,
  //adding props_map here to get all values
  props_map,
  apoc.map.fromPairs(collect(distinct [item_compare, props_map[field]])) AS value_map
WITH DISTINCT
  iOID as `Item OID`,
  CASE split(field, '-')[0]
  WHEN 'elem_nsExt' THEN '9VendorExt(NameSpace for Element)'
  WHEN 'elem_attExt' THEN '8VendorExt(Attribute for Element)'
  WHEN 'elemExt' THEN '7VendorExt(Element)'
  WHEN 'att_nsExt' THEN '6VendorExt(NameSpace for Attribute)'
  WHEN 'attExt' THEN '5VendorExt(Attribute)'
  WHEN 'itemterm' THEN '4Terms'
  WHEN 'alias' THEN '3Alias'
  WHEN 'desc' THEN '2Description'
  ELSE '1Identification'
END AS area,
  CASE WHEN split(field, '-')[0] IN ['desc', 'alias', 'itemterm', 'attExt','elem_attExt','elemExt','elem_nsExt','att_nsExt']
     THEN split(field, '-')[1]  
     ELSE field
END AS `Item attribute`,
replace(replace(toString(value_map['Base']), '<p>', ''), '</p>', '')   AS Base,
replace(replace(toString(value_map['Compare']), '<p>', ''), '</p>', '')  AS Compare
ORDER BY `Item OID`, area, `Item attribute`
WITH DISTINCT `Item OID`, area, `Item attribute`, Base, Compare,
CASE WHEN Base = Compare THEN 'N' ELSE CASE WHEN Base is null and Compare is null THEN 'N' ELSE 'Y' END END as __diff
WITH DISTINCT `Item OID`,substring(area,1) as Area, `Item attribute`, Base, Compare, __diff
return `Item OID`, Area, `Item attribute`, Base, Compare, __diff
 